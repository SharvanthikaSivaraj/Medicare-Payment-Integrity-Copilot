"""
Week 4, step 1: prepare coverage policies and clinical notes.

Inputs  data/interim/coverage/lcd_selected.csv   (Colab: coverage_download.ipynb)
        data/raw/mtsamples/mtsamples.csv           (Kaggle: Medical Transcriptions)
Outputs data/interim/coverage/policies.json      one policy per procedure, clean text by section
        data/interim/coverage/notes.csv          procedure notes for the 4 procedures
        reports/coverage_data.md                 what was selected

Usage (from the repo root):
    python src/coverage/prepare_coverage.py
"""

import html
import json
import re
from pathlib import Path

import pandas as pd

LCD_CSV = Path("data/interim/coverage/lcd_selected.csv")
NOTES_CSV = Path("data/raw/mtsamples/mtsamples.csv")
OUT_DIR = Path("data/interim/coverage")
REPORT = Path("reports/coverage_data.md")

# The 4 procedures. A note counts only if its title or description contains at least one
# "must" word AND at least one "any" word.
PROCEDURES = {
    "cataract": {
        "name": "Cataract surgery",
        "must": ["cataract"],
        "any": ["extraction", "phaco", "intraocular lens", "iol", "cataract surgery"],
    },
    "facet_joint": {
        "name": "Facet joint injection / medial branch block / radiofrequency ablation",
        "must": ["facet", "medial branch"],
        "any": ["injection", "block", "rhizotomy", "radiofrequency", "ablation"],
    },
    "epidural_steroid_injection": {
        "name": "Epidural steroid injection",
        "must": ["epidural"],
        "any": ["steroid", "injection", "esi"],
    },
    "blepharoplasty": {
        "name": "Blepharoplasty (eyelid surgery)",
        "must": ["blepharoplasty"],
        "any": [""],
    },
}

# LCD columns that hold the coverage rules (names from the CMS data dictionary).
# Any other long text column is kept too, so nothing important is lost.
PREFERRED_SECTIONS = ["indication", "doc_reqs", "util_guide", "coding_guidelines"]
MIN_NOTE_CHARS = 400


def html_to_text(raw: str) -> str:
    """Turn LCD HTML into readable text, keeping list items and paragraphs."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    t = re.sub(r"(?i)<li[^>]*>", "\n- ", t)
    t = re.sub(r"(?i)</(p|div|li|ul|ol|h\d|tr)>|<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    return "\n".join(line.strip() for line in t.splitlines()).strip()


def long_text_columns(lcd: pd.DataFrame) -> list[str]:
    return [c for c in lcd.columns if lcd[c].fillna("").str.len().mean() > 300]


def text_sections(lcd: pd.DataFrame) -> list[str]:
    """Only the sections that state coverage rules. Evidence reviews are left out on
    purpose: they are long and would bury the rules the model has to check."""
    present = [c for c in PREFERRED_SECTIONS if c in lcd.columns]
    return present or long_text_columns(lcd)


def build_policies() -> tuple[dict, list[str]]:
    lcd = pd.read_csv(LCD_CSV, dtype=str).fillna("")
    lcd.columns = lcd.columns.str.lower()
    sections = text_sections(lcd)
    policies = {}
    for topic in PROCEDURES:
        rows = lcd[lcd["topic"] == topic].copy()
        if rows.empty:
            continue
        rows["clean"] = rows.apply(
            lambda r: {s: html_to_text(r[s]) for s in sections if html_to_text(r[s])}, axis=1
        )
        rows["length"] = rows["clean"].map(lambda d: sum(len(v) for v in d.values()))
        # Several Medicare contractors publish near-identical LCDs; keep the most detailed one
        best = rows.sort_values("length", ascending=False).iloc[0]
        policies[topic] = {
            "procedure": PROCEDURES[topic]["name"],
            "lcd_id": best.get("lcd_id", ""),
            "lcd_version": best.get("lcd_version", ""),
            "title": best["title"],
            "alternatives": sorted(set(rows["lcd_id"]) - {best.get("lcd_id", "")}),
            "sections": best["clean"],
        }
    return policies, sections


def build_notes() -> pd.DataFrame:
    notes = pd.read_csv(NOTES_CSV, dtype=str).fillna("")
    notes.columns = [c.strip().lower() for c in notes.columns]
    if "unnamed: 0" in notes.columns:
        notes = notes.rename(columns={"unnamed: 0": "source_row"})
    else:
        notes["source_row"] = notes.index.astype(str)
    title = (notes["sample_name"] + " " + notes["description"]).str.lower()

    picked = []
    for topic, rule in PROCEDURES.items():
        mask = title.apply(lambda t: any(w in t for w in rule["must"]))
        mask &= title.apply(lambda t: any(w in t for w in rule["any"]))
        mask &= notes["transcription"].str.len() >= MIN_NOTE_CHARS
        picked.append(notes[mask].assign(topic=topic))

    out = pd.concat(picked, ignore_index=True)
    # The same note can be posted under several specialties in MTSamples
    out = out.drop_duplicates(subset=["topic", "transcription"]).reset_index(drop=True)
    out.insert(0, "note_id", [f"{t[:3].upper()}-{i:03d}" for i, t in enumerate(out["topic"])])
    return out[["note_id", "topic", "medical_specialty", "sample_name", "description",
                "transcription", "source_row"]]


def main() -> None:
    policies, sections = build_policies()
    notes = build_notes()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "policies.json").write_text(json.dumps(policies, indent=2))
    notes.to_csv(OUT_DIR / "notes.csv", index=False)

    lcd_cols = pd.read_csv(LCD_CSV, dtype=str, nrows=50).fillna("")
    lcd_cols.columns = lcd_cols.columns.str.lower()
    other_long = [c for c in long_text_columns(lcd_cols) if c not in sections]
    lines = ["# Coverage data", "",
             f"Policy text sections used: {', '.join(sections)}",
             f"Other long text columns (not used): {', '.join(other_long) or 'none'}", "",
             "| procedure | LCD | title | other versions | policy chars | procedure notes |",
             "| --- | --- | --- | --- | --- | --- |"]
    for topic, rule in PROCEDURES.items():
        p = policies.get(topic)
        n = int((notes["topic"] == topic).sum())
        if p:
            chars = sum(len(v) for v in p["sections"].values())
            lines.append(f"| {rule['name']} | L{p['lcd_id']} | {p['title']} | "
                         f"{len(p['alternatives'])} | {chars:,} | {n} |")
        else:
            lines.append(f"| {rule['name']} | none found | | | | {n} |")
    lines += ["", "## Section lengths per policy (characters)", "",
              "| procedure | " + " | ".join(sections) + " |",
              "| --- | " + " | ".join("---" for _ in sections) + " |"]
    for topic, p in policies.items():
        lines.append(f"| {topic} | " + " | ".join(f"{len(p['sections'].get(s, '')):,}" for s in sections) + " |")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print(text)
    print(f"Saved {OUT_DIR / 'policies.json'}, {OUT_DIR / 'notes.csv'} and {REPORT}")


if __name__ == "__main__":
    main()

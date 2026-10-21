"""
Week 4, step 3: check procedure notes against the reviewed coverage criteria with the local SLM.

Each kept criterion is asked as a plain yes/no QUESTION about the note (labels/criteria_*.json:
"question", "met_if", "if_not_mentioned"). The model only says what the note contains:
    yes / no        must quote the sentence from the note that shows it
    not_mentioned   the note is silent
The CODE then decides what that means for coverage. Small models handle "was IV sedation
used?" far better than double negatives such as "no sedation was used: met or not met?".

Evidence guard: a yes/no answer whose quote is missing or not found word for word in the
note is treated as not_mentioned.

Criterion status:
    met             answer == met_if (with verified evidence), or silent and if_not_mentioned == "met"
    not_met         the opposite answer, with verified evidence (the note contradicts the criterion)
    not_documented  otherwise
Verdict per note, from the procedure's decision rule:
    MEETS_COVERAGE         the rule is satisfied
    UNSUPPORTED            a required (all-of) criterion is not_met: the note contradicts coverage
    DOCUMENTATION_DEFICIT  otherwise (required evidence is missing)

Inputs  data/interim/coverage/notes.csv, labels/criteria_<procedure>.json (keep = true only)
Outputs data/processed/coverage_checks.jsonl   one line per note x criterion
        data/processed/coverage_verdicts.csv   one row per note
        reports/coverage_check.md

Usage (from the repo root, Ollama running):
    python src/coverage/check_coverage.py --limit 4      # quick test
    python src/coverage/check_coverage.py                # all notes
    python src/coverage/check_coverage.py --model qwen2.5:7b --tag qwen7b   # compare a model
"""

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

NOTES = Path("data/interim/coverage/notes.csv")
LABELS = Path("labels")
OLLAMA_URL = "http://localhost:11434/api/chat"
ANSWERS = ["yes", "no", "not_mentioned"]

SYSTEM = (
    "You read clinical notes and answer factual questions about what the note says. "
    "Use ONLY the note. Never assume facts that are not written. "
    "Evidence must be one sentence copied exactly from the note."
)

PROMPT = """Procedure: {procedure}

Clinical note:
<<<
{note}
>>>

Question: {question}

Answer with:
- "yes" if the note clearly says so. "evidence" = the sentence from the note that shows it.
- "no" if the note clearly says the opposite. "evidence" = the sentence from the note that shows it.
- "not_mentioned" if the note does not say. "evidence" = "".
The evidence must directly answer the question; do not quote unrelated sentences.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "enum": ANSWERS},
        "evidence": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["answer", "evidence", "reason"],
}


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[\s,]+", " ", text)  # MTSamples uses ", ," between sections
    return text.strip().strip('"').strip(" .")


def evidence_found(evidence: str, note: str) -> bool:
    e = normalize(evidence)
    return len(e) >= 10 and e in normalize(note)


def load_criteria() -> dict:
    out = {}
    for path in sorted(LABELS.glob("criteria_*.json")):
        d = json.loads(path.read_text())
        kept = [c for c in d["criteria"] if c.get("keep")]
        missing = [c["id"] for c in kept if not c.get("question")]
        if "decision_rule" not in d or missing:
            raise SystemExit(f"{path}: needs a decision_rule and a question for every kept criterion {missing}")
        out[path.stem.replace("criteria_", "")] = {"procedure": d["procedure"], "criteria": kept,
                                                  "rule": d["decision_rule"]}
    return out


def ask(model: str, prompt: str) -> dict:
    """One question to the model. num_predict caps the answer length: without it a small model
    can loop inside the evidence string forever. A question that still times out is retried
    once, then recorded as a model error (treated as not_mentioned) so one note cannot block the run."""
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "format": SCHEMA, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192, "num_predict": 400},
    }
    for attempt in (1, 2):
        try:
            r = requests.post(OLLAMA_URL, timeout=180, json=payload)
            r.raise_for_status()
            return json.loads(r.json()["message"]["content"])
        except (requests.Timeout, json.JSONDecodeError, KeyError):
            if attempt == 2:
                return {"answer": "not_mentioned", "evidence": "", "reason": "MODEL_ERROR: timeout or invalid output"}
    return {}


def to_status(criterion: dict, answer: str, evidence_ok: bool) -> str:
    """A required finding (met_if "yes") can only be documented or missing: a "no" answer to
    "is a pain score recorded?" means it is missing, not that the note contradicts coverage.
    Only a prohibited item (met_if "no") that the note shows IS present (answer "yes", with
    verified evidence) is a contradiction, e.g. "Was IV sedation used? yes"."""
    silent = "met" if criterion.get("if_not_mentioned") == "met" else "not_documented"
    if not evidence_ok:
        return silent
    if answer == criterion["met_if"]:
        return "met"
    if criterion["met_if"] == "no" and answer == "yes":
        return "not_met"
    return "not_documented"


def check_note(note: pd.Series, spec: dict, model: str) -> list[dict]:
    rows = []
    for c in spec["criteria"]:
        a = ask(model, PROMPT.format(procedure=spec["procedure"], note=note["transcription"],
                                     question=c["question"]))
        answer = a.get("answer") if a.get("answer") in ANSWERS else "not_mentioned"
        evidence = (a.get("evidence") or "").strip()
        claim = answer in ("yes", "no")
        ok = claim and evidence_found(evidence, note["transcription"])
        rows.append({
            "note_id": note["note_id"], "topic": note["topic"], "criterion_id": c["id"],
            "question": c["question"], "model_answer": answer, "met_if": c["met_if"],
            "status": to_status(c, answer, ok),
            "evidence": evidence if ok else "",
            "guard": ("ok" if ok else "no_evidence_given" if claim and not evidence
                      else "quote_not_in_note" if claim else ""),
            "rejected_evidence": evidence if claim and evidence and not ok else "",
            "reason": (a.get("reason") or "").strip(),
        })
    return rows


def verdict(rows: list[dict], rule: dict) -> tuple[str, str]:
    status = {r["criterion_id"]: r["status"] for r in rows}
    required = list(rule.get("all_of", []))
    groups = [list(g) for g in rule.get("any_of", [])]
    # Only a REQUIRED criterion that the note explicitly contradicts makes a note unsupported.
    # Alternatives in an "any of" group are not contradictions: the patient only needs one of them.
    contradicted = [cid for cid in required if status.get(cid) == "not_met"]
    if contradicted:
        return "UNSUPPORTED", "contradicted: " + ", ".join(contradicted)
    missing = [cid for cid in required if status.get(cid) != "met"]
    missing += [f"one of {'/'.join(g)}" for g in groups if not any(status.get(c) == "met" for c in g)]
    if missing:
        return "DOCUMENTATION_DEFICIT", "missing: " + ", ".join(missing)
    return "MEETS_COVERAGE", "all required criteria documented"


def md_table(df: pd.DataFrame, index: bool = True) -> str:
    df = df.reset_index() if index else df
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--tag", default="", help="suffix for output files, e.g. qwen7b")
    parser.add_argument("--limit", type=int, help="check only N notes (spread across procedures)")
    parser.add_argument("--topic", help="only one procedure, e.g. cataract")
    args = parser.parse_args()
    sfx = f"_{args.tag}" if args.tag else ""
    out_checks = Path(f"data/processed/coverage_checks{sfx}.jsonl")
    out_verdicts = Path(f"data/processed/coverage_verdicts{sfx}.csv")
    report = Path(f"reports/coverage_check{sfx}.md")

    try:
        requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()
    except requests.RequestException:
        raise SystemExit("Ollama is not running. Start it with: brew services start ollama")

    specs = load_criteria()
    notes = pd.read_csv(NOTES, dtype=str).fillna("")
    notes = notes[notes["topic"].isin(specs)]
    if args.topic:
        notes = notes[notes["topic"] == args.topic]
    if args.limit:
        per = max(1, args.limit // notes["topic"].nunique())
        notes = notes.groupby("topic", sort=False).head(per).head(args.limit)

    all_rows, verdicts, seconds = [], [], []
    for i, (_, note) in enumerate(notes.iterrows(), 1):
        spec = specs[note["topic"]]
        start = time.time()
        rows = check_note(note, spec, args.model)
        seconds.append(time.time() - start)
        v, why = verdict(rows, spec["rule"])
        all_rows += rows
        verdicts.append({"note_id": note["note_id"], "topic": note["topic"],
                         "sample_name": note["sample_name"].strip(), "verdict": v, "why": why,
                         "met": sum(r["status"] == "met" for r in rows),
                         "not_met": sum(r["status"] == "not_met" for r in rows),
                         "not_documented": sum(r["status"] == "not_documented" for r in rows),
                         "seconds": round(seconds[-1], 1), "model": args.model})
        print(f"  [{i}/{len(notes)}] {note['note_id']} {note['topic']}: {v} ({seconds[-1]:.0f}s) {why}")

    out_checks.parent.mkdir(parents=True, exist_ok=True)
    with open(out_checks, "w") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    vdf = pd.DataFrame(verdicts)
    vdf.to_csv(out_verdicts, index=False)

    checks = pd.DataFrame(all_rows)
    claims = checks[checks["model_answer"].isin(["yes", "no"])]
    names = dict(zip(checks["criterion_id"], checks["question"]))
    causes = []
    for why in vdf["why"]:
        if ": " in why:
            causes += [c.strip() for c in why.split(": ", 1)[1].split(",")]
    gaps = pd.Series(causes, dtype=str).value_counts().head(10).rename_axis("criterion_id").reset_index(name="notes")
    gaps.insert(1, "question", gaps["criterion_id"].map(lambda c: names.get(c, "(group of alternatives)")))

    lines = [
        "# Coverage check", "",
        f"Model: {args.model}, {len(vdf)} notes, {len(checks)} questions, "
        f"{sum(seconds) / max(1, len(seconds)):.0f} s per note on average.", "",
        "## Evidence guard", "",
        f"- Yes/no answers from the model: {len(claims)}",
        f"- Accepted with a verified quote: {int((claims['guard'] == 'ok').sum())}",
        f"- Rejected, no quote given: {int((claims['guard'] == 'no_evidence_given').sum())}",
        f"- Rejected, quote not found in the note: {int((claims['guard'] == 'quote_not_in_note').sum())}",
        f"- Model errors (timeout or invalid output, treated as not mentioned): "
        f"{int(checks['reason'].str.startswith('MODEL_ERROR').sum())}", "",
        "## Verdicts per procedure", "",
        md_table(vdf.pivot_table(index="topic", columns="verdict", values="note_id", aggfunc="count", fill_value=0)), "",
        "## Criterion statuses per procedure", "",
        md_table(checks.pivot_table(index="topic", columns="status", values="note_id", aggfunc="count", fill_value=0)), "",
        "## What most often caused a deficit or contradiction", "",
        md_table(gaps, index=False), "",
        "These are checks by a small model to support, not replace, a human reviewer.", "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines))
    print("\n" + "\n".join(lines))
    print(f"Saved {out_checks}, {out_verdicts} and {report}")


if __name__ == "__main__":
    main()

"""
Week 4, step 2: draft a checklist of coverage criteria from each policy with the local SLM.

The model reads the policy in chunks and lists the criteria Medicare requires, each with
an exact quote. Any quote that does not appear word for word in the policy is rejected
(the "evidence guard"), because small models sometimes invent text.

The output is a DRAFT. You review it by hand (see labels/criteria_review.md), set
"keep": false on anything wrong, and fix wording. The checker in step 3 uses only kept items.

Input   data/interim/coverage/policies.json
Output  labels/criteria_<procedure>.json
        labels/criteria_review.md

Needs Ollama running (brew services start ollama) and the model pulled.

Usage (from the repo root):
    python src/coverage/draft_criteria.py
    python src/coverage/draft_criteria.py --model llama3.2:3b --only cataract
"""

import argparse
import json
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

import requests

POLICIES = Path("data/interim/coverage/policies.json")
LABELS = Path("labels")
OLLAMA_URL = "http://localhost:11434/api/chat"

CHUNK_CHARS = 5000
OVERLAP_CHARS = 400
CRITERION_TYPES = ["indication", "limitation", "documentation"]

SYSTEM = (
    "You extract Medicare coverage criteria from policy text. Use ONLY the text you are given. "
    "Every criterion must include a quote copied exactly, character for character, from the text."
)

PROMPT = """Procedure: {procedure}

Policy text (part {part} of {parts}):
<<<
{chunk}
>>>

List the requirements in this text that decide whether Medicare covers the procedure for a patient:
- "indication": a condition or finding the patient must have
- "limitation": when it is NOT covered, or limits such as frequency or number of sessions
- "documentation": what must be written in the medical record

Rules:
- Each criterion is one short, checkable statement in plain English.
- "quote" must be copied exactly from the policy text above (one sentence or list item).
- Skip background, definitions, coding instructions and references.
- If this part has no requirements, return an empty list.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "type": {"type": "string", "enum": CRITERION_TYPES},
                    "quote": {"type": "string"},
                },
                "required": ["criterion", "type", "quote"],
            },
        }
    },
    "required": ["criteria"],
}


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"^[\s\-•*\d.)]+", "", text)  # leading bullets or numbering
    return re.sub(r"\s+", " ", text).strip().strip('"').strip()


def quote_found(quote: str, source: str) -> bool:
    """Evidence guard: the quote must appear in the policy (ignoring case and spacing)."""
    q = normalize(quote)
    return len(q) >= 15 and q in normalize(source)


def chunks(text: str) -> list[str]:
    """Split on paragraph breaks into pieces of about CHUNK_CHARS, with a little overlap."""
    paragraphs = text.split("\n\n")
    out, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) > CHUNK_CHARS:
            out.append(current)
            current = current[-OVERLAP_CHARS:]
        current = (current + "\n\n" + p).strip()
    if current:
        out.append(current)
    return out


def ask_model(model: str, prompt: str) -> list[dict]:
    response = requests.post(OLLAMA_URL, timeout=900, json={
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "format": SCHEMA,
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
    })
    response.raise_for_status()
    content = response.json()["message"]["content"]
    try:
        return json.loads(content).get("criteria", [])
    except json.JSONDecodeError:
        return []


def is_duplicate(item: dict, kept: list[dict]) -> bool:
    a = normalize(item["criterion"])
    for k in kept:
        if normalize(k["source_quote"]) == normalize(item["quote"]):
            return True
        if SequenceMatcher(None, a, normalize(k["criterion"])).ratio() > 0.85:
            return True
    return False


def draft(topic: str, policy: dict, model: str) -> tuple[list[dict], dict]:
    text = "\n\n".join(policy["sections"].values())
    parts = chunks(text)
    kept, stats = [], {"chunks": len(parts), "proposed": 0, "rejected_quote": 0, "duplicates": 0}
    for i, chunk in enumerate(parts, 1):
        start = time.time()
        items = ask_model(model, PROMPT.format(procedure=policy["procedure"], part=i,
                                               parts=len(parts), chunk=chunk))
        stats["proposed"] += len(items)
        for item in items:
            if not item.get("criterion") or not item.get("quote"):
                continue
            if not quote_found(item["quote"], chunk):
                stats["rejected_quote"] += 1
                continue
            if is_duplicate(item, kept):
                stats["duplicates"] += 1
                continue
            kept.append({
                "id": f"{topic[:3].upper()}-C{len(kept) + 1:02d}",
                "criterion": item["criterion"].strip(),
                "type": item.get("type") if item.get("type") in CRITERION_TYPES else "indication",
                "source_quote": re.sub(r"^[\s\-•*]+", "", item["quote"]).strip(),
                "keep": True,
                "reviewer_note": "",
            })
        print(f"    part {i}/{len(parts)}: {len(items)} proposed, {len(kept)} kept so far "
              f"({time.time() - start:.0f}s)")
    return kept, stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--only", help="run one procedure, e.g. cataract")
    args = parser.parse_args()

    try:
        requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()
    except requests.RequestException:
        raise SystemExit("Ollama is not running. Start it with: brew services start ollama")

    policies = json.loads(POLICIES.read_text())
    LABELS.mkdir(exist_ok=True)
    summary = []
    for topic, policy in policies.items():
        if args.only and topic != args.only:
            continue
        print(f"{topic}: L{policy['lcd_id']} {policy['title']}")
        criteria, stats = draft(topic, policy, args.model)
        out = {"procedure": policy["procedure"], "lcd_id": policy["lcd_id"], "title": policy["title"],
               "model": args.model, "status": "draft - review by hand", "criteria": criteria}
        (LABELS / f"criteria_{topic}.json").write_text(json.dumps(out, indent=2))
        summary.append((topic, policy, criteria, stats))

    lines = ["# Coverage criteria for review", "",
             "Drafted by a local SLM; every quote was verified to exist in the policy text.",
             "Review each item: edit the JSON file, set `keep` to false for wrong or irrelevant items, "
             "and fix wording if needed.", ""]
    for topic, policy, criteria, s in summary:
        lines += [f"## {policy['procedure']} (L{policy['lcd_id']})", "",
                  f"{s['chunks']} parts read, {s['proposed']} proposed, "
                  f"**{s['rejected_quote']} rejected for quotes not found in the policy**, "
                  f"{s['duplicates']} duplicates removed, {len(criteria)} kept.", "",
                  "| id | type | criterion | quote from policy |", "| --- | --- | --- | --- |"]
        for c in criteria:
            quote = c["source_quote"].replace("|", "/").replace("\n", " ")
            lines.append(f"| {c['id']} | {c['type']} | {c['criterion']} | {quote[:220]} |")
        lines.append("")
    (LABELS / "criteria_review.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

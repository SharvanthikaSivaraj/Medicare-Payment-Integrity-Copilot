"""
Week 5: measure how well the coverage checker agrees with your blind human labels.

Compares, on the questions you labeled in label_app.py:
  1. the model's raw answer            (what the SLM said)
  2. the answer after the evidence guard (unverified yes/no -> not_mentioned)
with your answer, and the resulting criterion STATUS (met / not_met / not_documented).

Reports accuracy, Cohen's kappa (agreement beyond chance), a confusion matrix, how much the
evidence guard helped, and the questions the model gets wrong most often.

Usage (from the repo root):
    python src/coverage/evaluate_coverage.py                 # default model run
    python src/coverage/evaluate_coverage.py --tag qwen7b    # a run saved with --tag qwen7b
"""

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

LABELS = Path("labels/human_labels.csv")
CRITERIA = Path("labels")
ANSWERS = ["yes", "no", "not_mentioned"]


def criterion_rules() -> dict:
    rules = {}
    for path in CRITERIA.glob("criteria_*.json"):
        for c in json.loads(path.read_text())["criteria"]:
            if c.get("keep"):
                rules[c["id"]] = c
    return rules


def to_status(c: dict, answer: str) -> str:
    """Same rule as check_coverage.py, for an answer whose evidence is trusted."""
    silent = "met" if c.get("if_not_mentioned") == "met" else "not_documented"
    if answer == c["met_if"]:
        return "met"
    if c["met_if"] == "no" and answer == "yes":
        return "not_met"
    return silent if answer == "not_mentioned" else "not_documented"


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def scores(truth: pd.Series, pred: pd.Series) -> tuple[float, float]:
    acc = (truth == pred).mean()
    kappa = cohen_kappa_score(truth, pred) if truth.nunique() > 1 or pred.nunique() > 1 else float("nan")
    return acc, kappa


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    sfx = f"_{args.tag}" if args.tag else ""
    checks_path = Path(f"data/processed/coverage_checks{sfx}.jsonl")
    report = Path(f"reports/coverage_eval{sfx}.md")

    labels = pd.read_csv(LABELS, dtype=str).fillna("")
    checks = pd.DataFrame([json.loads(l) for l in open(checks_path)])
    checks["key"] = checks["note_id"] + "|" + checks["criterion_id"]
    df = labels.merge(checks, on=["key", "note_id", "criterion_id"], how="inner")
    if df.empty:
        raise SystemExit("No overlap between your labels and this run. Label some questions first.")

    rules = criterion_rules()
    df = df[df["criterion_id"].isin(rules)]  # criteria removed in review are not scored
    df["guarded_answer"] = df.apply(lambda r: r["model_answer"] if r["guard"] == "ok" else "not_mentioned", axis=1)
    df["human_status"] = df.apply(lambda r: to_status(rules[r["criterion_id"]], r["human_answer"]), axis=1)

    raw_acc, raw_k = scores(df["human_answer"], df["model_answer"])
    g_acc, g_k = scores(df["human_answer"], df["guarded_answer"])
    s_acc, s_k = scores(df["human_status"], df["status"])

    confusion = pd.crosstab(df["human_answer"], df["guarded_answer"]).reindex(index=ANSWERS, columns=ANSWERS, fill_value=0)
    confusion.index = [f"human: {i}" for i in confusion.index]
    confusion = confusion.reset_index().rename(columns={"index": ""})

    # Did the guard help? Look at answers it rejected
    rejected = df[df["guard"].isin(["no_evidence_given", "quote_not_in_note"])]
    fixed = int((rejected["model_answer"] != rejected["human_answer"]).sum())

    # False contradictions are the costliest error: a covered service flagged as unsupported
    false_contra = df[(df["status"] == "not_met") & (df["human_status"] != "not_met")]
    missed_contra = df[(df["status"] != "not_met") & (df["human_status"] == "not_met")]

    per_q = (df.assign(correct=df["human_status"] == df["status"])
             .groupby(["criterion_id", "question"]).agg(labeled=("correct", "size"), correct=("correct", "sum"))
             .reset_index())
    per_q["accuracy"] = (per_q["correct"] / per_q["labeled"]).map("{:.0%}".format)
    per_q = per_q.sort_values(["correct", "labeled"], ascending=[True, False])

    model = df["model"].iat[0] if "model" in df else args.tag or "default"
    lines = [
        f"# Coverage checker vs human review{(' (' + args.tag + ')') if args.tag else ''}", "",
        f"{len(df)} blind-labeled questions across {df['note_id'].nunique()} notes.", "",
        "## Agreement with the human reviewer", "",
        "| what is compared | accuracy | Cohen's kappa |", "| --- | --- | --- |",
        f"| Model's raw answer | {raw_acc:.1%} | {raw_k:.2f} |",
        f"| Answer after the evidence guard | {g_acc:.1%} | {g_k:.2f} |",
        f"| Criterion status (met / not_met / not_documented) | {s_acc:.1%} | {s_k:.2f} |", "",
        "Kappa: 0 = chance agreement, 0.4-0.6 moderate, 0.6-0.8 substantial, above 0.8 near perfect.", "",
        "## Evidence guard", "",
        f"- The guard rejected {len(rejected)} of the labeled answers; in {fixed} of them the model's answer "
        "was also wrong according to the human, so rejecting it was correct.", "",
        "## Answers after the guard vs human (rows = human)", "", md_table(confusion), "",
        "## Contradiction errors (the costliest mistakes)", "",
        f"- False contradictions (checker says the note contradicts coverage, human disagrees): **{len(false_contra)}**",
        f"- Missed contradictions (human found one, checker did not): **{len(missed_contra)}**", "",
    ]
    if len(false_contra):
        lines += ["| note | criterion | model evidence | human comment |", "| --- | --- | --- | --- |"]
        for _, r in false_contra.iterrows():
            lines.append(f"| {r['note_id']} | {r['criterion_id']} | {r['evidence'][:120]} | {r['comment'][:80]} |")
        lines.append("")
    lines += ["## Accuracy per question (worst first)", "",
              md_table(per_q[["criterion_id", "question", "labeled", "accuracy"]]), ""]

    report.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"Saved {report}")


if __name__ == "__main__":
    main()

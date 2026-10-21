"""
Week 5: blind human labeling of coverage questions.

You answer a sample of the same yes / no / not_mentioned questions the model answered,
by reading the note yourself. The model's answer is HIDDEN so it cannot bias you.
src/coverage/evaluate_coverage.py then compares your labels with the model.

Sample (fixed once, saved to labels/label_sample.csv):
  every answer the code turned into a contradiction (not_met), every answer the evidence
  guard rejected, then a random mix of the rest, up to SAMPLE_SIZE questions.

Your labels are saved after every click to labels/human_labels.csv, so you can stop any time.

Usage (from the repo root):
    streamlit run src/coverage/label_app.py
"""

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

CHECKS = Path("data/processed/coverage_checks.jsonl")
NOTES = Path("data/interim/coverage/notes.csv")
SAMPLE = Path("labels/label_sample.csv")
LABELS = Path("labels/human_labels.csv")
SAMPLE_SIZE = 120
SEED = 42
CHOICES = ["yes", "no", "not_mentioned"]

st.set_page_config(page_title="Coverage labeling", page_icon="📝", layout="wide")


def make_sample() -> pd.DataFrame:
    checks = pd.DataFrame([json.loads(line) for line in open(CHECKS)])
    checks["key"] = checks["note_id"] + "|" + checks["criterion_id"]
    must = checks[(checks["status"] == "not_met") | checks["guard"].isin(["no_evidence_given", "quote_not_in_note"])]
    rest = checks.drop(must.index)
    n_rest = max(0, SAMPLE_SIZE - len(must))
    extra = rest.sample(n=min(n_rest, len(rest)), random_state=SEED)
    sample = pd.concat([must, extra]).sample(frac=1, random_state=SEED)  # shuffle so groups are mixed
    sample = sample[["key", "note_id", "topic", "criterion_id", "question"]].reset_index(drop=True)
    SAMPLE.parent.mkdir(exist_ok=True)
    sample.to_csv(SAMPLE, index=False)
    return sample


@st.cache_data
def load_notes() -> dict:
    notes = pd.read_csv(NOTES, dtype=str).fillna("")
    return dict(zip(notes["note_id"], notes["transcription"]))


def load_labels() -> pd.DataFrame:
    if LABELS.exists():
        return pd.read_csv(LABELS, dtype=str).fillna("")
    return pd.DataFrame(columns=["key", "note_id", "criterion_id", "human_answer", "human_evidence", "comment"])


def save_label(row: pd.Series, answer: str, evidence: str, comment: str) -> None:
    labels = load_labels()
    labels = labels[labels["key"] != row["key"]]
    new = pd.DataFrame([{"key": row["key"], "note_id": row["note_id"], "criterion_id": row["criterion_id"],
                         "human_answer": answer, "human_evidence": evidence.strip(), "comment": comment.strip()}])
    pd.concat([labels, new], ignore_index=True).to_csv(LABELS, index=False)


def readable(note: str) -> str:
    """MTSamples packs sections as 'HEADING: , text.,NEXT HEADING:'; put headings on new lines."""
    text = re.sub(r"\.,\s*", ".\n\n", note)
    text = re.sub(r":\s*,\s*", ": ", text)
    return text


if not CHECKS.exists():
    st.error("Run `python src/coverage/check_coverage.py` first.")
    st.stop()

sample = pd.read_csv(SAMPLE, dtype=str) if SAMPLE.exists() else make_sample()
notes = load_notes()
labels = load_labels()
done = set(labels["key"])

st.title("Blind labeling: coverage questions")
st.caption("Read the note and answer the question yourself. The model's answer is hidden on purpose.")
st.progress(len(done & set(sample["key"])) / len(sample),
            text=f"{len(done & set(sample['key']))} of {len(sample)} labeled")

if "i" not in st.session_state:
    todo = [k for k in sample["key"] if k not in done]
    st.session_state.i = int(sample.index[sample["key"] == todo[0]][0]) if todo else 0

i = st.session_state.i
row = sample.iloc[i]
existing = labels[labels["key"] == row["key"]]

left, right = st.columns([3, 2])
with left:
    st.subheader(f"Note {row['note_id']} · {row['topic'].replace('_', ' ')}")
    with st.container(height=560):
        st.text(readable(notes.get(row["note_id"], "(note not found)")))
with right:
    st.subheader(f"Question {i + 1} of {len(sample)} · {row['criterion_id']}")
    st.markdown(f"**{row['question']}**")
    st.markdown("- **yes**: the note clearly says so\n- **no**: the note clearly says the opposite\n"
                "- **not_mentioned**: the note does not say")
    default = existing["human_answer"].iat[0] if len(existing) else None
    answer = st.radio("Your answer", CHOICES, index=CHOICES.index(default) if default in CHOICES else None,
                      horizontal=True, key=f"a_{row['key']}")
    evidence = st.text_area("Supporting sentence from the note (optional)",
                            value=existing["human_evidence"].iat[0] if len(existing) else "",
                            key=f"e_{row['key']}", height=90)
    comment = st.text_input("Comment (optional)", value=existing["comment"].iat[0] if len(existing) else "",
                            key=f"c_{row['key']}")

    b1, b2, b3 = st.columns(3)
    if b1.button("← Previous", disabled=i == 0, width="stretch"):
        st.session_state.i = i - 1
        st.rerun()
    if b2.button("Save & next →", type="primary", disabled=answer is None, width="stretch"):
        save_label(row, answer, evidence, comment)
        st.session_state.i = min(i + 1, len(sample) - 1)
        st.rerun()
    if b3.button("Next unlabeled", width="stretch"):
        todo = [k for k in sample["key"] if k not in done]
        if todo:
            st.session_state.i = int(sample.index[sample["key"] == todo[0]][0])
            st.rerun()
    if len(existing):
        st.success(f"Saved: {existing['human_answer'].iat[0]}")

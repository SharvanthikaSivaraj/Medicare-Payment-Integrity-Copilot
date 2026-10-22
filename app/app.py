"""
Investigator dashboard (MVP): provider risk queue with reasons.

Usage (from the repo root):
    streamlit run app/app.py
"""

import hashlib
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DATA = Path("data/processed")
REPORT = Path("reports/model_eval.md")
NOTES = Path("data/interim/coverage/notes.csv")
COVERAGE_RUNS = {  # label -> file suffix written by check_coverage.py --tag
    "qwen2.5:7b (default)": "_qwen7b",
    "llama3.2:3b": "",
}
VERDICT_ICON = {"MEETS_COVERAGE": "🟢", "DOCUMENTATION_DEFICIT": "🟡", "UNSUPPORTED": "🔴"}
STATUS_ICON = {"met": "✅", "not_met": "⛔", "not_documented": "❔"}

st.set_page_config(page_title="Medicare Payment Integrity Copilot", page_icon="🩺", layout="wide")


@st.cache_data
def load_scores() -> tuple[pd.DataFrame, str]:
    files = sorted(DATA.glob("risk_scores_*.parquet"))
    if not files:
        return pd.DataFrame(), ""
    path = files[-1]
    df = duckdb.sql(f"SELECT * FROM '{path}' ORDER BY rank").df()
    df["provider_id"] = df["npi"].map(lambda n: "P-" + hashlib.sha256(str(n).encode()).hexdigest()[:8].upper())
    return df, path.stem.rsplit("_", 1)[-1]


def reasons_of(row: pd.Series) -> list[str]:
    return [row[f"reason_{i}"] for i in range(1, 6) if isinstance(row.get(f"reason_{i}"), str) and row[f"reason_{i}"]]


scores, year = load_scores()

st.title("Medicare Payment Integrity Copilot")
st.caption(f"Provider risk queue for {year} · ranked by a LightGBM model trained on earlier years")

if scores.empty:
    st.error("No risk scores found. Run `python src/models/train_models.py` first.")
    st.stop()

st.info(
    "Risk scores prioritize providers for review. They are statistical signals from public billing data, "
    "**not evidence of wrongdoing**. Provider IDs are masked by default.",
    icon="ℹ️",
)

# ---------- sidebar filters ----------
with st.sidebar:
    st.header("Filters")
    queue_size = st.select_slider("Review capacity (top N providers)", options=[100, 250, 500, 1000, 2500, 5000], value=1000)
    queue = scores[scores["rank"] <= queue_size]
    states = st.multiselect("State", sorted(queue["state"].dropna().unique()))
    specialties = st.multiselect("Specialty", sorted(queue["specialty"].dropna().unique()))
    show_npi = st.toggle("Show real NPIs (local use only)", value=False)

if states:
    queue = queue[queue["state"].isin(states)]
if specialties:
    queue = queue[queue["specialty"].isin(specialties)]

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Providers in queue", f"{len(queue):,}")
c2.metric("Later excluded: fraud", int(queue["label_fraud"].sum()))
c3.metric("Later excluded: any reason", int(queue["label_any"].sum()))
hit_rate = queue["label_any"].mean() if len(queue) else 0
c4.metric("Queue hit rate (any)", f"{hit_rate:.2%}")
st.caption("'Later excluded' uses exclusions announced after the scoring year, so it validates the ranking.")

tab_queue, tab_case, tab_docs, tab_model = st.tabs(
    ["Risk queue", "Provider case view", "Documentation check", "Model performance"])

# ---------- risk queue ----------
with tab_queue:
    left, right = st.columns([3, 1])
    with left:
        table = queue.assign(
            id=queue["npi"] if show_npi else queue["provider_id"],
            later_excluded=queue["label_any"].map({1: "yes", 0: ""}),
        )[["rank", "id", "specialty", "state", "risk_score", "reason_1", "reason_2", "later_excluded"]]
        st.dataframe(
            table, hide_index=True, width="stretch", height=520,
            column_config={
                "rank": st.column_config.NumberColumn("Rank", width="small"),
                "id": "Provider",
                "risk_score": st.column_config.ProgressColumn("Risk score", min_value=0.0, max_value=float(scores["risk_score"].max()), format="%.3f"),
                "reason_1": "Top reason",
                "reason_2": "Second reason",
                "later_excluded": st.column_config.TextColumn("Later excluded", width="small"),
            },
        )
    with right:
        st.subheader("Queue by specialty")
        st.bar_chart(queue["specialty"].value_counts().head(12), horizontal=True)

# ---------- case view ----------
with tab_case:
    if queue.empty:
        st.warning("No providers match the filters.")
    else:
        label = queue["npi"] if show_npi else queue["provider_id"]
        options = dict(zip(label + " · rank " + queue["rank"].astype(str) + " · " + queue["specialty"], queue.index))
        choice = st.selectbox("Provider", list(options))
        row = queue.loc[options[choice]]

        a, b, c = st.columns(3)
        a.metric("Rank", int(row["rank"]))
        b.metric("Risk score", f"{row['risk_score']:.3f}")
        c.metric("Later excluded", "yes" if row["label_any"] else "no")
        st.markdown(f"**{row['specialty']}**, {row['state']}")

        st.subheader("Why this provider was flagged")
        for i, reason in enumerate(reasons_of(row), 1):
            st.markdown(f"{i}. `{reason}`")
        st.caption("Reasons come from SHAP values: the features that pushed this provider's score up the most, "
                   "compared with peers of the same specialty and state.")

        if show_npi:
            st.link_button("Open in NPPES registry", f"https://npiregistry.cms.hhs.gov/provider-view/{row['npi']}")

# ---------- documentation check ----------
@st.cache_data
def load_coverage(suffix: str):
    verdict_path = DATA / f"coverage_verdicts{suffix}.csv"
    checks_path = DATA / f"coverage_checks{suffix}.jsonl"
    if not verdict_path.exists() or not checks_path.exists() or not NOTES.exists():
        return None, None, None
    verdicts = pd.read_csv(verdict_path, dtype=str).fillna("")
    checks = pd.read_json(checks_path, lines=True, dtype=False).fillna("")
    notes = pd.read_csv(NOTES, dtype=str).fillna("")
    return verdicts, checks, dict(zip(notes["note_id"], notes["transcription"]))


def highlight(note: str, quotes: list[str]) -> str:
    """Note text with the model's verified evidence sentences highlighted."""
    text = note.replace("$", "\\$").replace(".,", ".\n\n").replace(": ,", ":")
    for q in sorted({q for q in quotes if q}, key=len, reverse=True):
        q_safe = q.replace("$", "\\$").strip().rstrip(",")
        if q_safe and q_safe in text:
            text = text.replace(q_safe, f":orange-background[{q_safe}]")
    return text


with tab_docs:
    st.caption(
        "A local small language model checks procedure notes against Medicare coverage policies (LCDs). "
        "Every answer must quote the note; quotes that are not in the note are rejected by the evidence guard. "
        "Notes are public MTSamples transcriptions, not linked to the providers above."
    )
    available = {k: v for k, v in COVERAGE_RUNS.items() if (DATA / f"coverage_verdicts{v}.csv").exists()}
    if not available:
        st.warning("No coverage results yet. Run `python src/coverage/check_coverage.py` first.")
    else:
        run = st.radio("Model", list(available), horizontal=True)
        verdicts, checks, note_text = load_coverage(available[run])

        counts = verdicts["verdict"].value_counts()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Notes checked", len(verdicts))
        k2.metric("🟢 Meets coverage", int(counts.get("MEETS_COVERAGE", 0)))
        k3.metric("🟡 Documentation deficit", int(counts.get("DOCUMENTATION_DEFICIT", 0)))
        k4.metric("🔴 Unsupported", int(counts.get("UNSUPPORTED", 0)))

        order = ["MEETS_COVERAGE", "DOCUMENTATION_DEFICIT", "UNSUPPORTED"]
        by_topic = (verdicts.assign(procedure=verdicts["topic"].str.replace("_", " ").str.capitalize())
                    .pivot_table(index="procedure", columns="verdict", values="note_id",
                                 aggfunc="count", fill_value=0)
                    .reindex(columns=order, fill_value=0))
        by_topic.columns = ["Meets coverage", "Documentation deficit", "Unsupported"]
        st.bar_chart(by_topic, horizontal=True, color=["#2e9e5b", "#e0a526", "#d64545"],
                     x_label="", y_label="notes")

        f1, f2 = st.columns(2)
        topic = f1.selectbox("Procedure", ["All"] + sorted(verdicts["topic"].unique()))
        verdict_filter = f2.selectbox("Verdict", ["All", "UNSUPPORTED", "DOCUMENTATION_DEFICIT", "MEETS_COVERAGE"])
        shown = verdicts
        if topic != "All":
            shown = shown[shown["topic"] == topic]
        if verdict_filter != "All":
            shown = shown[shown["verdict"] == verdict_filter]

        if shown.empty:
            st.info("No notes match these filters.")
        else:
            labels = (shown["verdict"].map(VERDICT_ICON) + " " + shown["note_id"] + " · "
                      + shown["sample_name"])
            pick = st.selectbox("Note", list(labels), index=0)
            note_row = shown.iloc[list(labels).index(pick)]
            note_checks = checks[checks["note_id"] == note_row["note_id"]]

            st.markdown(f"### {VERDICT_ICON[note_row['verdict']]} {note_row['verdict'].replace('_', ' ').title()}")
            st.caption(note_row["why"])

            left, right = st.columns([1, 1])
            with left:
                st.subheader("Criteria")
                for _, c in note_checks.iterrows():
                    with st.container(border=True):
                        st.markdown(f"{STATUS_ICON.get(c['status'], '')} **{c['criterion_id']}**: {c['question']}")
                        st.caption(f"Model answer: {c['model_answer']} · status: {c['status'].replace('_', ' ')}")
                        if c["evidence"]:
                            st.markdown(f"> {c['evidence']}")
                        if c["rejected_evidence"]:
                            st.markdown(f":red[Rejected by evidence guard (not in the note):] ~~{c['rejected_evidence'][:200]}~~")
            with right:
                st.subheader("Clinical note")
                with st.container(height=640):
                    st.markdown(highlight(note_text.get(note_row["note_id"], ""), list(note_checks["evidence"])))

# ---------- model performance ----------
with tab_model:
    st.subheader("Provider risk model")
    if REPORT.exists():
        st.markdown(REPORT.read_text())
    else:
        st.warning("reports/model_eval.md not found.")
    st.divider()
    st.subheader("Documentation checker vs human review")
    eval_files = {"qwen2.5:7b": Path("reports/coverage_eval_qwen7b.md"), "llama3.2:3b": Path("reports/coverage_eval.md")}
    found = {k: v for k, v in eval_files.items() if v.exists()}
    if found:
        for name, tab in zip(found, st.tabs(list(found))):
            with tab:
                st.markdown(found[name].read_text())
    else:
        st.info("Run `python src/coverage/evaluate_coverage.py` to compare the checker with your labels.")

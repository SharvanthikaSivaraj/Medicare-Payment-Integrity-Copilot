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

tab_queue, tab_case, tab_model = st.tabs(["Risk queue", "Provider case view", "Model performance"])

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

# ---------- model performance ----------
with tab_model:
    if REPORT.exists():
        st.markdown(REPORT.read_text())
    else:
        st.warning("reports/model_eval.md not found.")

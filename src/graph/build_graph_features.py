"""
Graph and industry-payment features per provider per year.

Inputs  data/interim/openpayments/openpayments_<year>.parquet  (from the Colab notebook)
        data/interim/partd_drug/partd_drug_<year>.parquet      (brand-name prescribing)
        data/processed/features.parquet                         (for peer groups)
Output  data/processed/graph_features.parquet
        reports/graph_summary.md

Features (all start with op_; each also gets pct_ and z_ peer versions)
  op_total_usd             all industry payments received ($)
  op_payments              number of payments
  op_companies             number of distinct paying companies
  op_highvalue_usd         consulting, speaker/faculty, honoraria, royalty, ownership ($)
  op_food_usd              food and beverage ($)
  op_top_company_share     share of all $ from the single largest payer
  op_paid_drug_claim_share share of brand-name claims for drugs whose maker paid this provider
  op_paid_drug_cost        drug cost of those claims ($)
  op_comm_size             size of the provider's Louvain community in the
                           high-value company-provider network
  op_comm_top_company_share share of that community's high-value $ from its largest company

Year T features use payments and prescribing from year T only (no future data).

Usage (from the repo root):
    python src/graph/build_graph_features.py
"""

from pathlib import Path

import duckdb
import networkx as nx
import pandas as pd

INTERIM = Path("data/interim")
FEATURES = Path("data/processed/features.parquet")
OUT = Path("data/processed/graph_features.parquet")
REPORT = Path("reports/graph_summary.md")

HIGH_VALUE = ["%consulting%", "%compensation for services%", "%honoraria%",
              "%royalty%", "%ownership%", "%faculty or as a speaker%"]
MIN_EDGE_USD = 1000   # high-value payments below this are left out of the network
SEED = 42


def nature_filter(patterns: list[str]) -> str:
    return "(" + " OR ".join(f"LOWER(nature) LIKE '{p}'" for p in patterns) + ")"


def first_word(col: str) -> str:
    """First word of a drug name: 'HUMIRA(CF) PEN' -> 'HUMIRA'."""
    return f"REGEXP_EXTRACT({col}, '^[A-Z0-9-]+')"


def payment_features(con, year: int) -> None:
    op = INTERIM / "openpayments" / f"openpayments_{year}.parquet"
    drug = INTERIM / "partd_drug" / f"partd_drug_{year}.parquet"
    hv = nature_filter(HIGH_VALUE)
    con.execute(f"""
        CREATE OR REPLACE TABLE pay_{year} AS
        WITH by_company AS (
            SELECT npi, company, SUM(usd) AS usd FROM '{op}' GROUP BY npi, company
        ),
        top_company AS (
            SELECT npi, MAX(usd) / NULLIF(SUM(usd), 0) AS op_top_company_share
            FROM by_company GROUP BY npi
        )
        SELECT p.npi,
               {year} AS year,
               SUM(usd) AS op_total_usd,
               SUM(n_payments) AS op_payments,
               COUNT(DISTINCT company) AS op_companies,
               SUM(CASE WHEN {hv} THEN usd ELSE 0 END) AS op_highvalue_usd,
               SUM(CASE WHEN LOWER(nature) LIKE '%food%' THEN usd ELSE 0 END) AS op_food_usd,
               ANY_VALUE(t.op_top_company_share) AS op_top_company_share
        FROM '{op}' p JOIN top_company t USING (npi)
        GROUP BY p.npi
    """)
    # Brand claims for drugs whose maker paid this provider in the same year
    con.execute(f"""
        CREATE OR REPLACE TABLE align_{year} AS
        WITH paid_products AS (
            SELECT DISTINCT npi, {first_word('product')} AS word
            FROM '{op}' WHERE product IS NOT NULL AND product <> ''
        ),
        rx AS (
            SELECT npi, {first_word('brand')} AS word, claims, drug_cost FROM '{drug}'
        )
        SELECT rx.npi,
               SUM(CASE WHEN pp.word IS NOT NULL THEN claims ELSE 0 END) / NULLIF(SUM(claims), 0)
                   AS op_paid_drug_claim_share,
               SUM(CASE WHEN pp.word IS NOT NULL THEN drug_cost ELSE 0 END) AS op_paid_drug_cost
        FROM rx LEFT JOIN paid_products pp ON pp.npi = rx.npi AND pp.word = rx.word
        GROUP BY rx.npi
    """)


def community_features(con, year: int) -> pd.DataFrame:
    op = INTERIM / "openpayments" / f"openpayments_{year}.parquet"
    edges = con.execute(f"""
        SELECT npi, company, SUM(usd) AS usd
        FROM '{op}' WHERE {nature_filter(HIGH_VALUE)}
        GROUP BY npi, company HAVING SUM(usd) >= {MIN_EDGE_USD}
    """).df()
    if edges.empty:
        return pd.DataFrame(columns=["npi", "year", "op_comm_size", "op_comm_top_company_share"])

    g = nx.Graph()
    g.add_weighted_edges_from(
        (("P:" + n, "C:" + c, w) for n, c, w in edges.itertuples(index=False)), weight="weight"
    )
    print(f"    network {year}: {g.number_of_nodes():,} nodes, {g.number_of_edges():,} edges")
    communities = nx.community.louvain_communities(g, weight="weight", seed=SEED)

    community_of = {node: i for i, members in enumerate(communities) for node in members}
    edges["comm"] = edges["npi"].map(lambda n: community_of["P:" + n])
    comm_company = edges.groupby(["comm", "company"])["usd"].sum()
    comm_top_share = (comm_company.groupby(level=0).max() / comm_company.groupby(level=0).sum())
    comm_size = edges.groupby("comm")["npi"].nunique()

    providers = edges[["npi", "comm"]].drop_duplicates("npi")
    return pd.DataFrame({
        "npi": providers["npi"].to_numpy(),
        "year": year,
        "op_comm_size": providers["comm"].map(comm_size).to_numpy(),
        "op_comm_top_company_share": providers["comm"].map(comm_top_share).to_numpy(),
    })


def main() -> None:
    years = sorted(int(p.stem.rsplit("_", 1)[-1]) for p in (INTERIM / "openpayments").glob("*.parquet"))
    print(f"Years: {years}")
    con = duckdb.connect()
    Path("data/duckdb_tmp").mkdir(parents=True, exist_ok=True)
    con.execute("SET temp_directory = 'data/duckdb_tmp'")
    con.execute("SET preserve_insertion_order = false")

    comm_frames = []
    for year in years:
        print(f"  {year}: payment and alignment features")
        payment_features(con, year)
        print(f"  {year}: Louvain communities")
        comm_frames.append(community_features(con, year))
    comm = pd.concat(comm_frames, ignore_index=True)
    con.register("comm", comm)

    pay = " UNION ALL ".join(f"SELECT * FROM pay_{y}" for y in years)
    align = " UNION ALL ".join(f"SELECT *, {y} AS year FROM align_{y}" for y in years)

    raw = ["op_total_usd", "op_payments", "op_companies", "op_highvalue_usd", "op_food_usd",
           "op_top_company_share", "op_paid_drug_claim_share", "op_paid_drug_cost",
           "op_comm_size", "op_comm_top_company_share"]
    zero_if_missing = {"op_total_usd", "op_payments", "op_companies", "op_highvalue_usd",
                       "op_food_usd", "op_paid_drug_cost"}
    select_raw = ",\n".join(
        f"COALESCE({c}, 0) AS {c}" if c in zero_if_missing else c for c in raw
    )

    # One row per provider-year in the main feature table, with peer groups
    con.execute(f"""
        CREATE TABLE joined AS
        SELECT f.npi, f.year, f.peer_group,
               {select_raw}
        FROM (SELECT npi, year, peer_group FROM '{FEATURES}') f
        LEFT JOIN ({pay}) p USING (npi, year)
        LEFT JOIN ({align}) a USING (npi, year)
        LEFT JOIN comm c USING (npi, year)
    """)

    part = "PARTITION BY year, peer_group"
    norm = []
    for c in raw:
        norm.append(f"CASE WHEN {c} IS NULL THEN NULL ELSE "
                    f"PERCENT_RANK() OVER ({part}, ({c} IS NULL) ORDER BY {c}) END AS pct_{c}")
        norm.append(f"({c} - MEDIAN({c}) OVER ({part})) / NULLIF(1.4826 * MAD({c}) OVER ({part}), 0) AS z_{c}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (SELECT * EXCLUDE (peer_group), {', '.join(norm)} FROM joined)
        TO '{OUT}' (FORMAT parquet, COMPRESSION zstd)
    """)

    # Summary: payments and alignment for providers later excluded vs everyone else
    summary = con.execute(f"""
        SELECT f.split,
               CASE WHEN f.label_fraud = 1 THEN 'later excluded (fraud)' ELSE 'everyone else' END AS grp,
               COUNT(*) AS providers,
               ROUND(100.0 * AVG((g.op_total_usd > 0)::INT), 1) AS pct_paid,
               ROUND(MEDIAN(g.op_total_usd) FILTER (WHERE g.op_total_usd > 0)) AS median_usd_if_paid,
               ROUND(100.0 * AVG((g.op_highvalue_usd > 0)::INT), 1) AS pct_highvalue,
               ROUND(AVG(g.op_paid_drug_claim_share), 3) AS avg_paid_drug_share
        FROM '{FEATURES}' f JOIN '{OUT}' g USING (npi, year)
        GROUP BY ALL ORDER BY f.split DESC, grp
    """).fetchall()

    lines = ["# Graph and industry-payment features", "",
             f"- Years: {years}",
             f"- High-value payment types: {', '.join(p.strip('%') for p in HIGH_VALUE)}",
             f"- Network: company-provider links with >= ${MIN_EDGE_USD:,} high-value payments, Louvain communities", "",
             "| split | group | providers | % receiving payments | median $ if paid | % high-value | avg paid-drug claim share |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for s, grp, n, p, med, hvp, share in summary:
        lines.append(f"| {s} | {grp} | {n:,} | {p}% | {med if med is not None else '-'} | {hvp}% | {share} |")
    text = "\n".join(lines) + "\n"
    REPORT.write_text(text)
    print("\n" + text)
    print(f"Saved {OUT} and {REPORT}")


if __name__ == "__main__":
    main()

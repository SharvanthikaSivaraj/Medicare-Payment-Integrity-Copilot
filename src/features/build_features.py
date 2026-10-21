"""
Week 2: build one row per provider per year with peer-normalized features and
leakage-free labels.

Input   data/interim/partb_provider/*.parquet, data/interim/partd_provider/*.parquet,
        data/interim/leie/leie_updated.parquet
Output  data/processed/features.parquet
        reports/feature_summary.md

Design
- Universe: individual providers (entity code "I") in Part B and/or Part D.
- Peer group: same specialty + state when that group has >= 30 providers,
  otherwise the same specialty nationally.
- For every raw feature we add:
    pct_<feature>  percentile rank within the peer group (0 = lowest, 1 = highest)
    z_<feature>    robust z-score: (value - peer median) / (1.4826 * peer MAD)
- Labels for a row in year T (only exclusions AFTER year T, so no leakage):
    label_any    excluded in year T+1 or T+2, any exclusion type
    label_fraud  same window, fraud-related types (1128a1, 1128a3, 1128b1, 1128b7)
    label_rx     same window, controlled-substance types (1128a4, 1128b3)
  Providers already excluded in or before year T are dropped from that year.
- Split: the latest year is "test", earlier years are "train".

Usage (from the repo root):
    python src/features/build_features.py
"""

from pathlib import Path

import duckdb

INTERIM = Path("data/interim")
OUT = Path("data/processed/features.parquet")
REPORT = Path("reports/feature_summary.md")

MIN_PEERS = 30
FRAUD_TYPES = ("1128a1", "1128a3", "1128b1", "1128b7")
RX_TYPES = ("1128a4", "1128b3")


def num(col: str) -> str:
    """Cast a text column to a number; CMS uses blanks for suppressed values."""
    return f"TRY_CAST(NULLIF(TRIM({col}), '') AS DOUBLE)"


def ratio(a: str, b: str) -> str:
    return f"{num(a)} / NULLIF({num(b)}, 0)"


# Raw features: name -> (SQL expression, description)
PARTB_FEATURES = {
    "b_benes": (num("tot_benes"), "Part B: Medicare patients seen"),
    "b_hcpcs_codes": (num("tot_hcpcs_cds"), "Part B: distinct procedure codes billed"),
    "b_srvcs_per_bene": (ratio("tot_srvcs", "tot_benes"), "Part B: services per patient"),
    "b_pay_per_bene": (ratio("tot_mdcr_pymt_amt", "tot_benes"), "Part B: Medicare payment per patient ($)"),
    "b_stdzd_per_bene": (ratio("tot_mdcr_stdzd_amt", "tot_benes"), "Part B: geography-standardized payment per patient ($)"),
    "b_charge_to_allowed": (ratio("tot_sbmtd_chrg", "tot_mdcr_alowd_amt"), "Part B: submitted charges / allowed amount"),
    "b_srvcs_per_code": (ratio("tot_srvcs", "tot_hcpcs_cds"), "Part B: services per distinct code (repetitive billing)"),
    "b_drug_pay_share": (ratio("drug_mdcr_pymt_amt", "tot_mdcr_pymt_amt"), "Part B: share of payment from drugs"),
    "b_dual_share": (ratio("bene_dual_cnt", "tot_benes"), "Part B: share of patients dual-eligible (Medicare + Medicaid)"),
    "b_under65_share": (ratio("bene_age_lt_65_cnt", "tot_benes"), "Part B: share of patients under 65"),
    "b_risk_score": (num("bene_avg_risk_scre"), "Part B: average patient risk score"),
}

PARTD_FEATURES = {
    "d_claims": (num("tot_clms"), "Part D: prescription claims"),
    "d_benes": (num("tot_benes"), "Part D: patients with prescriptions"),
    "d_claims_per_bene": (ratio("tot_clms", "tot_benes"), "Part D: claims per patient"),
    "d_cost_per_claim": (ratio("tot_drug_cst", "tot_clms"), "Part D: drug cost per claim ($)"),
    "d_cost_per_bene": (ratio("tot_drug_cst", "tot_benes"), "Part D: drug cost per patient ($)"),
    "d_supply_per_claim": (ratio("tot_day_suply", "tot_clms"), "Part D: days supplied per claim"),
    "d_brand_share": (ratio("brnd_tot_clms", "tot_clms"), "Part D: share of brand-name claims"),
    "d_lis_share": (ratio("lis_tot_clms", "tot_clms"), "Part D: share of low-income-subsidy claims"),
    "d_opioid_share": (ratio("opioid_tot_clms", "tot_clms"), "Part D: share of opioid claims"),
    "d_opioid_la_share": (ratio("opioid_la_tot_clms", "opioid_tot_clms"), "Part D: long-acting share of opioid claims"),
    "d_opioid_supply_per_claim": (ratio("opioid_tot_suply", "opioid_tot_clms"), "Part D: days supplied per opioid claim"),
    "d_antipsych_65_share": (ratio("antpsyct_ge65_tot_clms", "ge65_tot_clms"), "Part D: antipsychotic share of 65+ claims"),
}

# Year-over-year growth features (current / previous year - 1)
GROWTH = {
    "g_b_pay_per_bene": ("b_pay_per_bene", "Growth in Part B payment per patient vs last year"),
    "g_b_benes": ("b_benes", "Growth in Part B patients vs last year"),
    "g_d_cost_per_bene": ("d_cost_per_bene", "Growth in Part D cost per patient vs last year"),
}

RAW_FEATURES = list(PARTB_FEATURES) + list(PARTD_FEATURES) + list(GROWTH)


def year_sql(year: int) -> str:
    b_path = INTERIM / "partb_provider" / f"partb_provider_{year}.parquet"
    d_path = INTERIM / "partd_provider" / f"partd_provider_{year}.parquet"
    b_cols = ",\n            ".join(f"{expr} AS {name}" for name, (expr, _) in PARTB_FEATURES.items())
    d_cols = ",\n            ".join(f"{expr} AS {name}" for name, (expr, _) in PARTD_FEATURES.items())
    all_feats = ", ".join(list(PARTB_FEATURES) + list(PARTD_FEATURES))
    return f"""
    WITH b AS (
        SELECT TRIM(rndrng_npi) AS npi,
               rndrng_prvdr_type AS b_type,
               rndrng_prvdr_state_abrvtn AS b_state,
               rndrng_prvdr_ent_cd AS b_ent,
            {b_cols}
        FROM '{b_path}'
    ),
    d AS (
        SELECT TRIM(prscrbr_npi) AS npi,
               prscrbr_type AS d_type,
               prscrbr_state_abrvtn AS d_state,
               prscrbr_ent_cd AS d_ent,
            {d_cols}
        FROM '{d_path}'
    )
    SELECT COALESCE(b.npi, d.npi) AS npi,
           {year} AS year,
           COALESCE(b.b_type, d.d_type) AS specialty,
           COALESCE(b.b_state, d.d_state) AS state,
           b.npi IS NOT NULL AS has_partb,
           d.npi IS NOT NULL AS has_partd,
           {all_feats}
    FROM b FULL OUTER JOIN d ON b.npi = d.npi
    WHERE COALESCE(b.b_ent, d.d_ent) = 'I'
      AND COALESCE(b.b_type, d.d_type) IS NOT NULL
      AND COALESCE(b.b_state, d.d_state) IS NOT NULL
    """


def available_years() -> list[int]:
    def years(src):
        return {int(p.stem.rsplit("_", 1)[-1]) for p in (INTERIM / src).glob("*.parquet")}
    return sorted(years("partb_provider") & years("partd_provider"))


def main() -> None:
    years = available_years()
    if not years:
        raise SystemExit("No matching Part B / Part D years in data/interim/")
    test_year = years[-1]
    print(f"Years: {years}  (train: {years[:-1]}, test: {test_year})")

    con = duckdb.connect()
    # ~4M provider-years: let DuckDB spill to disk instead of running out of memory
    Path("data/duckdb_tmp").mkdir(parents=True, exist_ok=True)
    con.execute("SET temp_directory = 'data/duckdb_tmp'")
    con.execute("SET preserve_insertion_order = false")

    # 1. Raw provider-year table
    print("Building provider-year table ...")
    union = "\nUNION ALL\n".join(f"SELECT * FROM ({year_sql(y)})" for y in years)
    con.execute(f"CREATE TABLE base AS {union}")

    # 2. Year-over-year growth (only when the previous year is the calendar year before)
    growth_cols = ",\n".join(
        f"""CASE WHEN LAG(year) OVER w = year - 1
                 THEN {src} / NULLIF(LAG({src}) OVER w, 0) - 1 END AS {name}"""
        for name, (src, _) in GROWTH.items()
    )
    con.execute(f"""
        CREATE TABLE base2 AS
        SELECT *, {growth_cols}
        FROM base
        WINDOW w AS (PARTITION BY npi ORDER BY year)
    """)

    # 3. Peer groups
    con.execute(f"""
        CREATE TABLE peers AS
        SELECT *,
               CASE WHEN COUNT(*) OVER (PARTITION BY year, specialty, state) >= {MIN_PEERS}
                    THEN specialty || ' | ' || state
                    ELSE specialty || ' | ALL' END AS peer_group
        FROM base2
    """)

    # 4. Percentile ranks and robust z-scores within peer group
    print("Computing peer-normalized features ...")
    norm_cols = []
    for f in RAW_FEATURES:
        part = "PARTITION BY year, peer_group"
        norm_cols.append(
            f"CASE WHEN {f} IS NULL THEN NULL ELSE "
            f"PERCENT_RANK() OVER ({part}, ({f} IS NULL) ORDER BY {f}) END AS pct_{f}"
        )
        norm_cols.append(
            f"({f} - MEDIAN({f}) OVER ({part})) / "
            f"NULLIF(1.4826 * MAD({f}) OVER ({part}), 0) AS z_{f}"
        )
    con.execute(f"""
        CREATE TABLE normed AS
        SELECT *, COUNT(*) OVER (PARTITION BY year, peer_group) AS peer_group_size,
               {', '.join(norm_cols)}
        FROM peers
    """)

    # 5. Labels from the exclusion list
    leie_path = INTERIM / "leie" / "leie_updated.parquet"
    fraud = ", ".join(f"'{t}'" for t in FRAUD_TYPES)
    rx = ", ".join(f"'{t}'" for t in RX_TYPES)
    con.execute(f"""
        CREATE TABLE excl AS
        SELECT TRIM(npi) AS npi,
               TRY_CAST(SUBSTR(TRIM(excldate), 1, 4) AS INTEGER) AS excl_year,
               LOWER(REPLACE(TRIM(excltype), ' ', '')) AS excl_type
        FROM '{leie_path}'
        WHERE REGEXP_FULL_MATCH(TRIM(npi), '[0-9]{{10}}') AND TRIM(npi) <> '0000000000'
    """)
    con.execute(f"""
        CREATE TABLE labelled AS
        SELECT n.*,
               CASE WHEN n.year = {test_year} THEN 'test' ELSE 'train' END AS split,
               COALESCE(BOOL_OR(e.excl_year BETWEEN n.year + 1 AND n.year + 2), FALSE)::INT AS label_any,
               COALESCE(BOOL_OR(e.excl_year BETWEEN n.year + 1 AND n.year + 2
                                AND e.excl_type IN ({fraud})), FALSE)::INT AS label_fraud,
               COALESCE(BOOL_OR(e.excl_year BETWEEN n.year + 1 AND n.year + 2
                                AND e.excl_type IN ({rx})), FALSE)::INT AS label_rx,
               COALESCE(BOOL_OR(e.excl_year <= n.year), FALSE) AS already_excluded
        FROM normed n
        LEFT JOIN excl e ON e.npi = n.npi
        GROUP BY ALL
    """)
    dropped = con.execute("SELECT COUNT(*) FROM labelled WHERE already_excluded").fetchone()[0]

    # 6. Save
    OUT.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (SELECT * EXCLUDE (already_excluded) FROM labelled WHERE NOT already_excluded
              ORDER BY year, npi)
        TO '{OUT}' (FORMAT parquet, COMPRESSION zstd)
    """)

    # 7. Summary report
    counts = con.execute(f"""
        SELECT year, split, COUNT(*) AS providers,
               SUM(label_any) AS label_any, SUM(label_fraud) AS label_fraud, SUM(label_rx) AS label_rx,
               ROUND(100.0 * SUM(label_fraud) / COUNT(*), 4) AS fraud_pct,
               COUNT(DISTINCT peer_group) AS peer_groups
        FROM '{OUT}' GROUP BY year, split ORDER BY year
    """).fetchall()
    n_cols = len(con.execute(f"DESCRIBE SELECT * FROM '{OUT}'").fetchall())
    missing = con.execute(
        "SELECT " + ", ".join(f"ROUND(100.0 * AVG(({f} IS NULL)::INT), 1)" for f in RAW_FEATURES)
        + f" FROM '{OUT}'"
    ).fetchone()

    lines = [
        "# Feature summary", "",
        f"- Years: {years}; train = {years[:-1]}, test = {test_year}",
        f"- Peer group: specialty + state if >= {MIN_PEERS} providers, else specialty nationally",
        f"- Rows dropped because the provider was already excluded: {dropped:,}",
        f"- Columns in features.parquet: {n_cols}", "",
        "## Rows and labels per year", "",
        "| year | split | providers | label_any | label_fraud | label_rx | fraud % | peer groups |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for y, s, p, la, lf, lr, fp, pg in counts:
        lines.append(f"| {y} | {s} | {p:,} | {la} | {lf} | {lr} | {fp} | {pg:,} |")
    lines += ["", "## Feature dictionary", "",
              "Each feature also has `pct_` (peer percentile) and `z_` (peer robust z-score) versions.", "",
              "| feature | description | missing % |", "| --- | --- | --- |"]
    descriptions = {**{k: v[1] for k, v in PARTB_FEATURES.items()},
                    **{k: v[1] for k, v in PARTD_FEATURES.items()},
                    **{k: v[1] for k, v in GROWTH.items()}}
    for f, m in zip(RAW_FEATURES, missing):
        lines.append(f"| {f} | {descriptions[f]} | {m} |")

    text = "\n".join(lines) + "\n"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("\n" + text)
    print(f"Saved {OUT} and {REPORT}")


if __name__ == "__main__":
    main()

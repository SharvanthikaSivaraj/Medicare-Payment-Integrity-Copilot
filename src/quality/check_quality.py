"""
Data-quality checks for the raw Parquet files in data/interim/.

What it checks
1. Row and column counts per file
2. NPI validity: 10 digits and a correct check digit (Luhn with the 80840 prefix)
3. Duplicate NPIs within each provider-year file
4. Missing values in key columns (NPI, provider type, state)
5. Negative values in numeric total columns (tot_*)
6. LEIE exclusion list: how many exclusions have an NPI, how many match a
   billing provider, and how many were billing BEFORE their exclusion date
   (only those can become training labels without leakage)

Writes reports/data_quality.md and prints the same report.

Usage (from the repo root):
    python src/quality/check_quality.py
"""

from pathlib import Path

import duckdb
import pandas as pd

INTERIM = Path("data/interim")
REPORT = Path("reports/data_quality.md")
BILLING_SOURCES = ["partb_provider", "partd_provider"]


# ---------- helpers ----------

def luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def npi_valid(npis: pd.Series) -> pd.Series:
    """True where the NPI is 10 digits with a valid check digit."""
    s = npis.fillna("").astype(str).str.strip()
    ten_digits = s.str.fullmatch(r"\d{10}")
    return ten_digits & s.map(lambda n: len(n) == 10 and n.isdigit() and luhn_ok("80840" + n))


def find_col(columns: list[str], *needles: str) -> str | None:
    """First column whose name contains all needles."""
    for c in columns:
        if all(n in c for n in needles):
            return c
    return None


def md_table(rows: list[dict]) -> str:
    if not rows:
        return "_none_\n"
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(r[h]) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.2f}%" if whole else "n/a"


# ---------- checks ----------

def check_billing_file(con, path: Path) -> tuple[dict, list[dict], pd.DataFrame]:
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{path}'").fetchall()]
    npi_col = find_col(cols, "npi")
    type_col = find_col(cols, "prvdr_type") or find_col(cols, "prscrbr_type") or find_col(cols, "type")
    state_col = find_col(cols, "state_abrvtn") or find_col(cols, "state")
    num_cols = [c for c in cols if c.startswith("tot_")]

    keep = [c for c in [npi_col, type_col, state_col] if c] + num_cols
    df = con.execute(f"SELECT {', '.join(keep)} FROM '{path}'").df()
    n = len(df)

    valid = npi_valid(df[npi_col])
    dupes = int(df[npi_col].duplicated().sum())

    summary = {
        "file": path.stem,
        "rows": f"{n:,}",
        "cols": len(cols),
        "invalid NPI": f"{int((~valid).sum()):,} ({pct(int((~valid).sum()), n)})",
        "duplicate NPI": f"{dupes:,}",
        "missing type": f"{int(df[type_col].isna().sum()):,}" if type_col else "no column",
        "missing state": f"{int(df[state_col].isna().sum()):,}" if state_col else "no column",
    }

    negatives = []
    for c in num_cols:
        vals = pd.to_numeric(df[c], errors="coerce")
        neg = int((vals < 0).sum())
        not_numeric = int(vals.isna().sum() - df[c].isna().sum())
        if neg or not_numeric:
            negatives.append({"file": path.stem, "column": c, "negative": neg, "non-numeric text": not_numeric})

    year = int(path.stem.rsplit("_", 1)[-1])
    npis = pd.DataFrame({"npi": df.loc[valid, npi_col].astype(str).str.strip(), "year": year})
    return summary, negatives, npis


def check_leie(con, path: Path, billing: pd.DataFrame) -> list[str]:
    df = con.execute(f"SELECT * FROM '{path}'").df()
    n = len(df)
    npi = df["npi"].fillna("").astype(str).str.strip()
    has_npi = npi.str.fullmatch(r"\d{10}") & (npi != "0000000000")
    valid = has_npi & npi_valid(npi)

    excl_year = pd.to_numeric(df["excldate"].astype(str).str[:4], errors="coerce")
    leie = pd.DataFrame({"npi": npi[valid], "excl_year": excl_year[valid]}).dropna()
    leie = leie.groupby("npi", as_index=False)["excl_year"].min()

    first_bill = billing.groupby("npi", as_index=False)["year"].min()
    matched = leie.merge(first_bill, on="npi")
    usable = matched[matched["year"] < matched["excl_year"]]

    lines = [
        f"- Total exclusion records: {n:,}",
        f"- Records with an NPI: {int(has_npi.sum()):,} ({pct(int(has_npi.sum()), n)})",
        f"- Records with a valid NPI: {int(valid.sum()):,}",
        f"- Unique excluded NPIs: {len(leie):,}",
        f"- Excluded NPIs found in billing data (any year): {len(matched):,}",
        f"- **Usable labels** (billed before exclusion year): {len(usable):,}",
        "",
        "Usable labels by exclusion year:",
        "",
    ]
    by_year = usable["excl_year"].astype(int).value_counts().sort_index()
    lines.append(md_table([{"exclusion year": y, "providers": c} for y, c in by_year.items()]))

    if "excltype" in df.columns:
        types = df.loc[valid & npi.isin(usable["npi"]), "excltype"].value_counts().head(8)
        lines += ["Most common exclusion types among usable labels:", ""]
        lines.append(md_table([{"exclusion type": t, "records": c} for t, c in types.items()]))
    return lines


def main() -> None:
    con = duckdb.connect()
    summaries, negatives, all_npis = [], [], []

    for source in BILLING_SOURCES:
        for path in sorted((INTERIM / source).glob("*.parquet")):
            print(f"checking {path} ...")
            s, neg, npis = check_billing_file(con, path)
            summaries.append(s)
            negatives += neg
            all_npis.append(npis)

    billing = pd.concat(all_npis, ignore_index=True)

    report = ["# Data quality report", "", "## Billing files", "", md_table(summaries)]
    report += ["## Numeric column problems", "",
               "Columns with negative values or text that is not a number:", "", md_table(negatives)]

    leie_path = INTERIM / "leie" / "leie_updated.parquet"
    if leie_path.exists():
        print(f"checking {leie_path} ...")
        report += ["## LEIE exclusion list", ""] + check_leie(con, leie_path, billing)

    text = "\n".join(report)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("\n" + text)
    print(f"\nSaved {REPORT}")


if __name__ == "__main__":
    main()

"""
Convert every raw CSV in data/raw/ into Parquet in data/interim/ using DuckDB,
and print a row-count summary.

Usage (from the repo root):
    python src/ingest/to_parquet.py
"""

from pathlib import Path

import duckdb

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/interim")


def convert(con: duckdb.DuckDBPyConnection, csv_path: Path) -> tuple[str, int, int]:
    out = OUT_DIR / csv_path.parent.name / (csv_path.stem + ".parquet")
    out.parent.mkdir(parents=True, exist_ok=True)

    # Read every column as text first: CMS files have mixed types and codes with
    # leading zeros (NPIs, ZIP codes). We cast types later, in SQL, on purpose.
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv('{csv_path}', header = true, all_varchar = true,
                                   normalize_names = true)
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
        """
    )
    rows = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
    cols = len(con.execute(f"DESCRIBE SELECT * FROM '{out}'").fetchall())
    return str(out), rows, cols


def main() -> None:
    csvs = sorted(RAW_DIR.rglob("*.csv"))
    if not csvs:
        print("No CSV files in data/raw/. Run src/ingest/download.py first.")
        return

    con = duckdb.connect()
    print(f"{'file':<55} {'rows':>12} {'cols':>6}")
    for csv_path in csvs:
        out, rows, cols = convert(con, csv_path)
        print(f"{out:<55} {rows:>12,} {cols:>6}")


if __name__ == "__main__":
    main()

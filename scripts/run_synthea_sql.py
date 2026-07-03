"""
Run the Synthea SQL extraction pipeline against a SQLite database.
Executes all 6 SQL scripts in order, then exports results to CSV.

Usage:
    python scripts/run_synthea_sql.py
    python scripts/run_synthea_sql.py --db data/synthea.db
"""

import os
import sys
import glob
import sqlite3
import argparse
import pandas as pd


def run_sql_file(conn, sql_path):
    """Execute a SQL file, splitting on semicolons."""
    filename = os.path.basename(sql_path)
    print(f"\n{'='*60}")
    print(f"Running: {filename}")
    print(f"{'='*60}")

    with open(sql_path, encoding='utf-8') as f:
        raw = f.read()

    # Split into individual statements.
    # Key subtlety: lines like  "  AS INTEGER) >= 18;   -- Adults only"
    # end with an inline comment, not ';', so we strip the comment portion
    # before checking the boundary — but keep the code portion for the stmt.
    statements = []
    current = []
    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue  # skip pure comment lines
        # Strip inline comment for boundary detection only
        code_part = line.split("--")[0] if "--" in line else line
        current.append(code_part)
        if code_part.rstrip().endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt and stmt != ";":
                statements.append(stmt)
            current = []
    # Flush any unterminated trailing statement
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    for i, stmt in enumerate(statements):
        try:
            cursor = conn.execute(stmt)
            conn.commit()

            # Print SELECT results
            if cursor.description:
                cols = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                if rows:
                    df = pd.DataFrame(rows, columns=cols)
                    print(df.to_string(index=False))
                    print()

            print(f"  Statement {i+1}/{len(statements)} [OK]")
        except Exception as e:
            print(f"  Statement {i+1}/{len(statements)} [!!] -- {e}")


def export_tables(conn, output_dir):
    """Export derived tables to CSV for the Python pipeline."""
    print(f"\n{'='*60}")
    print("Exporting tables to CSV...")
    print(f"{'='*60}")

    exports = {
        "synthea_derived_cohort":           "cohort.csv",
        "synthea_derived_static_features":  "static_features.csv",
        "synthea_derived_timeseries":       "timeseries.csv",
        "synthea_derived_clinical_notes":   "clinical_notes.csv",
        "synthea_derived_comorbidities":    "comorbidities.csv",
    }

    for table, csv_name in exports.items():
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            out_path = os.path.join(output_dir, csv_name)
            df.to_csv(out_path, index=False)
            print(f"  [OK] {table:45s} -> {csv_name} ({len(df):,} rows)")
        except Exception as e:
            print(f"  [!!] {table:45s} -- {e}")


def main():
    parser = argparse.ArgumentParser(description="Run Synthea SQL pipeline")
    parser.add_argument("--db", default="data/synthea.db",
                        help="Path to SQLite database")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, args.db)
    sql_dir = os.path.join(project_root, "scripts", "sql", "synthea")
    output_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        print("Run this first:  python scripts/load_synthea_db.py")
        sys.exit(1)

    conn = sqlite3.connect(db_path)

    # Execute SQL scripts in order
    sql_files = sorted(glob.glob(os.path.join(sql_dir, "*.sql")))
    if not sql_files:
        print(f"ERROR: No SQL files found in {sql_dir}")
        sys.exit(1)

    print(f"Database: {db_path}")
    print(f"SQL scripts: {len(sql_files)} files in {sql_dir}")

    for sql_file in sql_files:
        run_sql_file(conn, sql_file)

    # Export to CSV
    export_tables(conn, output_dir)

    # Print final summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")

    try:
        n = conn.execute("SELECT COUNT(*) FROM synthea_derived_cohort").fetchone()[0]
        m = conn.execute("SELECT SUM(mortality) FROM synthea_derived_cohort").fetchone()[0]
        print(f"  Cohort size:    {n:,} patients")
        print(f"  Deaths:         {m:,} ({100*m/n:.1f}%)")

        ts = conn.execute("SELECT COUNT(*) FROM synthea_derived_timeseries").fetchone()[0]
        print(f"  Timeseries:     {ts:,} rows ({ts//max(n,1)} per patient)")

        notes = conn.execute("SELECT COUNT(*) FROM synthea_derived_clinical_notes").fetchone()[0]
        print(f"  Clinical notes: {notes:,}")
    except Exception:
        pass

    print(f"\n  Exported CSVs in: {output_dir}")
    print(f"  Next step: python scripts/feature_pipeline_sql.py")

    conn.close()


if __name__ == "__main__":
    main()

"""
Load Synthea CSV files into a SQLite database.
No external database installation required — SQLite ships with Python.

Usage:
    python scripts/load_synthea_db.py
    python scripts/load_synthea_db.py --csv-dir data/synthea/csv --db data/synthea.db
"""

import os
import sys
import glob
import sqlite3
import argparse
import pandas as pd

# Synthea tables we need for the ICU mortality project
REQUIRED_TABLES = [
    "patients",
    "encounters",
    "observations",
    "conditions",
    "medications",
    "procedures",
    "allergies",
]


def find_csv_dir(base_dir):
    """Locate the directory containing Synthea CSVs."""
    candidates = [
        base_dir,
        os.path.join(base_dir, "csv"),
        os.path.join(base_dir, "output", "csv"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            csvs = [f for f in os.listdir(d) if f.endswith(".csv")]
            if csvs:
                return d
    return None


def load_csv_to_sqlite(csv_dir, db_path):
    """Load all Synthea CSVs into SQLite tables."""
    print(f"Database: {db_path}")
    print(f"CSV dir:  {csv_dir}\n")

    conn = sqlite3.connect(db_path)

    csv_files = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))

    if not csv_files:
        print("ERROR: No CSV files found. Download Synthea data first:")
        print("  python scripts/generate_synthea.py")
        sys.exit(1)

    loaded = []
    for csv_path in csv_files:
        table_name = os.path.splitext(os.path.basename(csv_path))[0].lower()

        print(f"Loading {table_name}...", end=" ")
        try:
            df = pd.read_csv(csv_path, low_memory=False)
            # Normalize column names to uppercase (Synthea convention)
            df.columns = [c.upper() for c in df.columns]
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"{len(df):,} rows × {len(df.columns)} columns")
            loaded.append(table_name)
        except Exception as e:
            print(f"FAILED — {e}")

    # Create indexes for performance
    print("\nCreating indexes...")
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_patients_id ON patients(ID);",
        "CREATE INDEX IF NOT EXISTS idx_encounters_id ON encounters(ID);",
        "CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(PATIENT);",
        "CREATE INDEX IF NOT EXISTS idx_encounters_class ON encounters(ENCOUNTERCLASS);",
        "CREATE INDEX IF NOT EXISTS idx_observations_patient ON observations(PATIENT);",
        "CREATE INDEX IF NOT EXISTS idx_observations_encounter ON observations(ENCOUNTER);",
        "CREATE INDEX IF NOT EXISTS idx_observations_code ON observations(CODE);",
        "CREATE INDEX IF NOT EXISTS idx_conditions_patient ON conditions(PATIENT);",
        "CREATE INDEX IF NOT EXISTS idx_conditions_encounter ON conditions(ENCOUNTER);",
        "CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(PATIENT);",
        "CREATE INDEX IF NOT EXISTS idx_medications_encounter ON medications(ENCOUNTER);",
    ]
    for stmt in index_statements:
        try:
            conn.execute(stmt)
        except Exception:
            pass
    conn.commit()

    # Verify required tables
    print(f"\n{'='*50}")
    print("VERIFICATION")
    print(f"{'='*50}")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    db_tables = [row[0] for row in cursor.fetchall()]

    for table in REQUIRED_TABLES:
        if table in db_tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  [OK] {table:20s} {count:>10,} rows")
        else:
            print(f"  [!!] {table:20s} MISSING")

    conn.close()
    print(f"\n[OK] Database ready: {db_path}")
    print(f"  Total tables loaded: {len(loaded)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Synthea CSVs into SQLite")
    parser.add_argument("--csv-dir", default=None, help="Path to Synthea CSV directory")
    parser.add_argument("--db", default="data/synthea.db", help="Output SQLite database path")
    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, args.db)

    if args.csv_dir:
        csv_dir = args.csv_dir
    else:
        csv_dir = find_csv_dir(os.path.join(project_root, "data", "synthea"))

    if csv_dir is None:
        print("ERROR: Cannot find Synthea CSV files.")
        print("Download first:  python scripts/generate_synthea.py")
        print("Or specify:      python scripts/load_synthea_db.py --csv-dir /path/to/csvs")
        sys.exit(1)

    load_csv_to_sqlite(csv_dir, db_path)

"""
Run MIMIC-IV SQL extraction pipeline against a PostgreSQL database.
Executes all SQL scripts in order and exports results to CSV.

Usage:
    python scripts/run_sql_pipeline.py --host localhost --dbname mimic --user postgres
    python scripts/run_sql_pipeline.py --bigquery --project your-gcp-project
"""

import argparse
import os
import sys
import glob


def run_postgresql(sql_dir, output_dir, host, port, dbname, user, password):
    """Execute SQL scripts against PostgreSQL MIMIC-IV installation."""
    try:
        import psycopg2
        import pandas as pd
    except ImportError:
        print("Install required packages: pip install psycopg2-binary pandas")
        sys.exit(1)

    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname,
        user=user, password=password
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Get SQL files in order
    sql_files = sorted(glob.glob(os.path.join(sql_dir, "*.sql")))

    for sql_file in sql_files:
        filename = os.path.basename(sql_file)
        print(f"\n{'='*60}")
        print(f"Running: {filename}")
        print(f"{'='*60}")

        with open(sql_file) as f:
            sql = f.read()

        # Split on semicolons and execute each statement
        statements = [s.strip() for s in sql.split(";") if s.strip()
                      and not s.strip().startswith("--")]

        for i, stmt in enumerate(statements):
            try:
                cursor.execute(stmt)
                if cursor.description:
                    cols = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    if rows:
                        df = pd.DataFrame(rows, columns=cols)
                        print(df.to_string(index=False))
                print(f"  Statement {i+1}/{len(statements)} ✓")
            except Exception as e:
                print(f"  Statement {i+1} failed: {e}")
                conn.rollback()
                conn.autocommit = True

    # Export derived tables to CSV
    print(f"\n{'='*60}")
    print("Exporting derived tables to CSV...")
    print(f"{'='*60}")

    export_tables = [
        ("mimiciv_derived.cohort", "cohort_mimic.csv"),
        ("mimiciv_derived.static_features", "static_features_mimic.csv"),
        ("mimiciv_derived.timeseries_combined", "timeseries_mimic.csv"),
        ("mimiciv_derived.notes_combined", "notes_mimic.csv"),
    ]

    for table, csv_name in export_tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            output_path = os.path.join(output_dir, csv_name)
            df.to_csv(output_path, index=False)
            print(f"  {table} → {csv_name} ({len(df):,} rows)")
        except Exception as e:
            print(f"  Failed to export {table}: {e}")

    cursor.close()
    conn.close()
    print("\n✓ SQL pipeline complete.")


def run_bigquery(sql_dir, output_dir, project):
    """Execute SQL scripts against BigQuery MIMIC-IV."""
    try:
        from google.cloud import bigquery
        import pandas as pd
    except ImportError:
        print("Install: pip install google-cloud-bigquery pandas pyarrow")
        sys.exit(1)

    client = bigquery.Client(project=project)
    sql_files = sorted(glob.glob(os.path.join(sql_dir, "*.sql")))

    for sql_file in sql_files:
        filename = os.path.basename(sql_file)
        print(f"\nRunning: {filename}")

        with open(sql_file) as f:
            sql = f.read()

        # Adapt PostgreSQL syntax to BigQuery
        sql = sql.replace("mimiciv_icu.", "physionet-data.mimiciv_3_1_icu.")
        sql = sql.replace("mimiciv_hosp.", "physionet-data.mimiciv_3_1_hosp.")
        sql = sql.replace("mimiciv_note.", "physionet-data.mimiciv_3_1_note.")
        sql = sql.replace("mimiciv_derived.", f"{project}.mimiciv_derived.")
        sql = sql.replace("ILIKE", "LIKE")  # BigQuery uses LIKE
        sql = sql.replace("::INT", "")
        sql = sql.replace("::NUMERIC", "")
        sql = sql.replace("DROP TABLE IF EXISTS", "CREATE OR REPLACE TABLE")
        sql = sql.replace("CREATE TABLE", "CREATE OR REPLACE TABLE")

        # Execute each statement
        statements = [s.strip() for s in sql.split(";") if s.strip()
                      and not s.strip().startswith("--")]

        for stmt in statements:
            try:
                job = client.query(stmt)
                result = job.result()
                print(f"  ✓ ({job.total_bytes_processed or 0:,} bytes processed)")
            except Exception as e:
                print(f"  ✗ {e}")

    print("\n✓ BigQuery pipeline complete.")
    print(f"  Export tables from {project}.mimiciv_derived to CSV manually or via bq extract.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MIMIC-IV SQL pipeline")
    parser.add_argument("--bigquery", action="store_true", help="Use BigQuery instead of PostgreSQL")
    parser.add_argument("--project", default="", help="GCP project for BigQuery")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port")
    parser.add_argument("--dbname", default="mimic", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--password", default="", help="Database password")
    args = parser.parse_args()

    sql_dir = os.path.join(os.path.dirname(__file__), "sql")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)

    if args.bigquery:
        if not args.project:
            print("Error: --project required for BigQuery mode")
            sys.exit(1)
        run_bigquery(sql_dir, output_dir, args.project)
    else:
        run_postgresql(sql_dir, output_dir,
                       args.host, args.port, args.dbname,
                       args.user, args.password)

"""
Generate or download Synthea synthetic EHR data for development.
This allows you to build and test the full pipeline immediately
while waiting for MIMIC-IV access.
"""

import os
import subprocess
import sys

SYNTHEA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "synthea")
os.makedirs(SYNTHEA_DIR, exist_ok=True)


def download_synthea_csv():
    """Download pre-generated Synthea CSV samples."""
    import urllib.request
    import zipfile

    url = "https://synthetichealth.github.io/synthea-sample-data/downloads/latest/synthea_sample_data_csv_latest.zip"
    zip_path = os.path.join(SYNTHEA_DIR, "synthea_sample.zip")

    print("Downloading Synthea sample data (~50MB)...")
    print(f"  URL: {url}")
    print(f"  Destination: {zip_path}")

    try:
        urllib.request.urlretrieve(url, zip_path)
        print("  Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(SYNTHEA_DIR)
        os.remove(zip_path)
        print("  [OK] Synthea data downloaded and extracted.")
    except Exception as e:
        print(f"  [!!] Download failed: {e}")
        print("\n  Alternative: Generate data locally with Synthea:")
        print("    1. Install Java 17+")
        print("    2. git clone https://github.com/synthetichealth/synthea.git")
        print("    3. cd synthea && ./run_synthea -p 10000 -s 42 --exporter.csv.export=true")
        print("    4. Copy output/csv/* to data/synthea/csv/")


def generate_synthea_local(population_size=10000, seed=42):
    """Generate Synthea data locally (requires Java 17+ and cloned repo)."""
    synthea_repo = os.path.join(os.path.dirname(__file__), "..", "synthea")

    if not os.path.exists(synthea_repo):
        print("Cloning Synthea repository...")
        subprocess.run(["git", "clone", "https://github.com/synthetichealth/synthea.git",
                        synthea_repo], check=True)

    print(f"Generating {population_size} synthetic patients (seed={seed})...")
    subprocess.run(
        [os.path.join(synthea_repo, "run_synthea"),
         "-p", str(population_size), "-s", str(seed),
         "--exporter.csv.export=true",
         f"--exporter.baseDirectory={SYNTHEA_DIR}"],
        cwd=synthea_repo, check=True
    )
    print("[OK] Synthea data generated.")


def list_synthea_files():
    """List available Synthea CSV files."""
    csv_dir = os.path.join(SYNTHEA_DIR, "csv")
    if not os.path.exists(csv_dir):
        # Check if CSVs are directly in SYNTHEA_DIR
        csv_files = [f for f in os.listdir(SYNTHEA_DIR) if f.endswith(".csv")]
        if csv_files:
            csv_dir = SYNTHEA_DIR
        else:
            print("No Synthea CSV files found. Run download or generate first.")
            return

    print(f"\nSynthea CSV files in {csv_dir}:")
    for f in sorted(os.listdir(csv_dir)):
        if f.endswith(".csv"):
            size = os.path.getsize(os.path.join(csv_dir, f))
            print(f"  {f:30s} ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    print("=" * 60)
    print("Synthea Synthetic EHR Data Generator")
    print("=" * 60)

    if "--local" in sys.argv:
        pop = int(sys.argv[sys.argv.index("--local") + 1]) if len(sys.argv) > sys.argv.index("--local") + 1 else 10000
        generate_synthea_local(population_size=pop)
    else:
        download_synthea_csv()

    list_synthea_files()

"""
==============================================================================
Live Verification Suite: Bronze Staging & Silver Conformance Layers
Target: Databricks Serverless Compute (Unity Catalog: dwbi_catalog)
==============================================================================
Run via:
    .\\.venv-dbx\\Scripts\\python.exe tests/verify_bronze_silver.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root & 03_ETL in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "03_ETL"))

try:
    from databricks.connect import DatabricksSession
except ImportError:
    print("[ERROR] databricks-connect is not installed in the active environment.")
    print("Please run this script using .\\.venv-dbx\\Scripts\\python.exe")
    sys.exit(1)


def main():
    profile_name = "dbc-4a52ea97-5404"
    catalog_name = "dwbi_catalog"

    print("=" * 75)
    print(" LIVE DATABRICKS VERIFICATION: BRONZE & SILVER MEDALLION LAYERS")
    print(f" Databricks Profile: [{profile_name}] | Target Catalog: [{catalog_name}]")
    print("=" * 75)

    print("\n[1/5] Establishing Spark Connect session to Databricks Serverless...")
    try:
        spark = DatabricksSession.builder.profile(profile_name).serverless().getOrCreate()
        current_user = spark.sql("SELECT current_user()").collect()[0][0]
        print(f"      ✓ Connected successfully as user: {current_user}")
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        print("Tip: Run 'databricks auth login --profile dbc-4a52ea97-5404' to refresh authentication.")
        sys.exit(1)

    # 1. Verify Bronze Staging Tables
    print("\n[2/5] Auditing Bronze Staging Tables (dwbi_catalog.bronze_staging)...")
    bronze_tables = [
        "raw_eia860_plant",
        "raw_eia860_generator",
        "raw_eia860_enviro_assoc",
        "raw_eia923_monthly_generation",
        "raw_noaa_isd_weather",
        "raw_epa_hourly_emissions",
        "raw_epa_eia_crosswalk",
        "raw_eia930_hourly_grid",
        "raw_noaa_isd_station_history"
    ]
    bronze_ok = True
    for tbl in bronze_tables:
        try:
            count = spark.sql(f"SELECT COUNT(*) FROM {catalog_name}.bronze_staging.{tbl}").collect()[0][0]
            status = "✓ OK" if count > 0 else "! EMPTY"
            print(f"      {status:<8} {tbl:<35} : {count:>5} records")
            if count == 0:
                bronze_ok = False
        except Exception as e:
            print(f"      ✗ FAIL   {tbl:<35} : Missing or Unreadable ({e})")
            bronze_ok = False

    # 2. Verify Silver Conformed Tables
    print("\n[3/5] Auditing Silver Conformed Tables (dwbi_catalog.silver_conformed)...")
    silver_tables = [
        "silver_plants_master",
        "silver_generators_scd2",
        "silver_monthly_generation",
        "silver_weather_hourly",
        "silver_emissions_cems",
        "silver_grid_hourly",
        "cleaning_step_log"
    ]
    silver_ok = True
    for tbl in silver_tables:
        try:
            count = spark.sql(f"SELECT COUNT(*) FROM {catalog_name}.silver_conformed.{tbl}").collect()[0][0]
            status = "✓ OK" if count > 0 else "! EMPTY"
            print(f"      {status:<8} {tbl:<35} : {count:>5} records")
            if count == 0:
                silver_ok = False
        except Exception as e:
            print(f"      ✗ FAIL   {tbl:<35} : Missing or Unreadable ({e})")
            silver_ok = False

    # 3. Check Quarantine Dead-Letter Table
    print("\n[4/5] Checking Dead-Letter Quarantine (dwbi_catalog.quarantine.rejected_records)...")
    try:
        q_count = spark.sql(f"SELECT COUNT(*) FROM {catalog_name}.quarantine.rejected_records").collect()[0][0]
        print(f"      ✓ OK     Total Quarantined Anomalies      : {q_count:>5} records logged")
    except Exception as e:
        print(f"      ✗ FAIL   Quarantine table unreadable: {e}")

    # 4. Check Pipeline Audit Log in Bronze
    print("\n[5/5] Checking Master Pipeline Execution Status (dwbi_catalog.bronze_staging.etl_run_log)...")
    try:
        audit_df = spark.sql(f"""
            SELECT batch_id, pipeline_step, records_read, records_inserted, records_rejected, execution_status, start_time
            FROM {catalog_name}.bronze_staging.etl_run_log
            ORDER BY run_id DESC
            LIMIT 5
        """).collect()
        for row in audit_df:
            step = row["pipeline_step"]
            status = row["execution_status"]
            read_cnt = row["records_read"]
            ins_cnt = row["records_inserted"]
            rej_cnt = row["records_rejected"]
            print(f"      Step: {step:<25} | Status: {status:<8} | Read: {read_cnt:>4} | Inserted: {ins_cnt:>4} | Rejected: {rej_cnt:>2}")
    except Exception as e:
        print(f"      ✗ Could not read audit run log: {e}")

    # Summary
    print("\n" + "=" * 75)
    if bronze_ok and silver_ok:
        print(" [RESULT: ALL CHECKS PASSED] Bronze & Silver layers are fully operational in Databricks!")
    else:
        print(" [RESULT: WARNING] Some tables are missing or empty. See logs above.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

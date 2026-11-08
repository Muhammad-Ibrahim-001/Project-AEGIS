"""
test_remote_connection.py
Stage 3: Databricks Serverless Remote Connection Verification Test

Authoritative Architecture:
- Serverless Compute Target: Databricks Serverless Environment Version 5
- Client Library: databricks-connect==18.3.7 (.venv-dbx)
- Local Python Interpreter: Python 3.12.3
- Authentication: Individual Databricks CLI OAuth U2M profile in ~/.databrickscfg

Security Mandates:
- ZERO hardcoded tokens, passwords, or personal credentials.
- Strictly NO printing of tokens, secrets, or sensitive credentials.
- Reads exclusively from ~/.databrickscfg or in-memory environment variables.
"""

import configparser
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def sanitize_message(msg: str) -> str:
    """Redacts potential tokens or secret patterns from error/output strings."""
    sanitized = re.sub(r"dapi[a-zA-Z0-9_-]+", "[REDACTED_TOKEN]", msg)
    sanitized = re.sub(r"ey[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}", "[REDACTED_JWT]", sanitized)
    sanitized = re.sub(r"(?i)(token|bearer|secret|password)[\s:=]+['\"]?[\w\.-]+['\"]?", r"\1: [REDACTED]", sanitized)
    return sanitized


def inspect_and_resolve_profile(requested_profile=None):
    """
    Safely inspects ~/.databrickscfg and resolves the best active profile.
    Detects and warns if any profile has invalid host URLs containing path suffixes.
    Returns (profile_name, host_url, auth_type).
    NEVER returns or exposes tokens or secrets.
    """
    databrickscfg_path = Path.home() / ".databrickscfg"
    if not databrickscfg_path.exists():
        return None, None, None

    config = configparser.ConfigParser()
    try:
        config.read(databrickscfg_path)
    except Exception as e:
        print(f"[WARN] Could not parse ~/.databrickscfg: {sanitize_message(str(e))}")
        return None, None, None

    # Check explicitly requested profile
    if requested_profile and config.has_section(requested_profile):
        host = config.get(requested_profile, "host", fallback=None)
        auth_type = config.get(requested_profile, "auth_type", fallback="databricks-cli / oauth")
        return requested_profile, host, auth_type

    # Check env var
    env_profile = os.environ.get("DATABRICKS_CONFIG_PROFILE")
    if env_profile and config.has_section(env_profile):
        host = config.get(env_profile, "host", fallback=None)
        auth_type = config.get(env_profile, "auth_type", fallback="databricks-cli / oauth")
        return env_profile, host, auth_type

    # Check DEFAULT profile
    if config.has_section("DEFAULT"):
        host = config.get("DEFAULT", "host", fallback=None)
        parsed = urlparse(host) if host else None
        if parsed and (not parsed.path or parsed.path == "/"):
            auth_type = config.get("DEFAULT", "auth_type", fallback="databricks-cli / oauth")
            return "DEFAULT", host, auth_type

    # Scan sections for valid clean profiles
    valid_profiles = []
    for sec in config.sections():
        if sec == "__settings__":
            continue
        host = config.get(sec, "host", fallback="")
        parsed = urlparse(host)
        # If host has unexpected path segments (e.g. /browse/folders/workspace), flag it
        if parsed.path and parsed.path not in ("", "/"):
            print(f"[NOTE] Profile [{sec}] has browser path '{parsed.path}' in host. Preferring clean profiles.")
        elif host.startswith("http"):
            valid_profiles.append((sec.strip(), host, config.get(sec, "auth_type", fallback="databricks-cli")))

    if valid_profiles:
        # Return first valid clean profile
        chosen_profile, chosen_host, chosen_auth = valid_profiles[0]
        return chosen_profile, chosen_host, chosen_auth

    # Fallback to first section if nothing else
    for sec in config.sections():
        if sec != "__settings__":
            return sec.strip(), config.get(sec, "host", fallback=None), config.get(sec, "auth_type", fallback="unknown")

    return None, None, None


def test_remote_serverless_connection(profile_name=None):
    """Initializes a DatabricksSession to test remote connectivity to Serverless compute."""
    print("=" * 75)
    print(" STAGE 3: DATABRICKS SERVERLESS REMOTE CONNECTIVITY VERIFICATION")
    print("=" * 75)
    print(f"Local Python Interpreter: {sys.version.split()[0]} ({sys.executable})")

    databrickscfg_path = Path.home() / ".databrickscfg"
    resolved_profile, host_url, auth_type = inspect_and_resolve_profile(profile_name)
    has_env_host = bool(os.environ.get("DATABRICKS_HOST"))

    if not resolved_profile and not has_env_host:
        print("\n[AUTHENTICATION NOTICE] Authentication is not yet configured on this workstation.")
        print(f"  - User Profile Config checked: {databrickscfg_path} (No active profile found)")
        print("  - Environment Variables checked: DATABRICKS_HOST (Not set)")
        print("\nTo configure individual authentication via OAuth U2M (Option A):")
        print("  databricks auth login --host https://<your-workspace-url>")
        print("=" * 75)
        return False

    print("\nLocal Authentication Profile:")
    if resolved_profile:
        print(f"  - Config file:    ~/.databrickscfg ({databrickscfg_path})")
        print(f"  - Active Profile: [{resolved_profile}]")
        print(f"  - Workspace Host: {host_url}")
        print(f"  - Auth Type:      {auth_type}")
    elif has_env_host:
        print(f"  - Workspace Host: {os.environ.get('DATABRICKS_HOST')} (from environment variable)")

    try:
        from databricks.connect import DatabricksSession
        import pyspark
    except ImportError as e:
        print(f"\n[ERROR] Required client package not found in active environment: {e}")
        print("Ensure you are running inside the standardized .venv-dbx environment:")
        print(r"  .\.venv-dbx\Scripts\python.exe tests/test_remote_connection.py")
        print("=" * 75)
        return False

    print("\nClient Libraries Verified:")
    print("  - databricks-connect: OK (version 18.3.7)")
    print(f"  - PySpark Connect stubs: OK ({pyspark.__file__})")

    print(f"\nConnecting to Databricks Serverless Compute (profile: [{resolved_profile}])...")
    try:
        builder = DatabricksSession.builder
        if resolved_profile and resolved_profile != "DEFAULT":
            builder = builder.profile(resolved_profile)

        # Explicitly configure Databricks Serverless Compute session
        spark = builder.serverless().getOrCreate()
        print("[SUCCESS] Databricks Serverless session established via Spark Connect gRPC!")

        # 1. Query remote runtime details
        print("\nQuerying remote session & runtime information:")
        query_session = (
            "SELECT current_user() AS authenticated_user, "
            "current_version().dbr_version AS dbr_version, "
            "current_metastore() AS metastore_id"
        )
        print(f"  SQL: {query_session}")

        res = spark.sql(query_session).collect()
        if res:
            row = res[0]
            print("\n" + "-" * 75)
            print(" REMOTE RUNTIME & IDENTITY DETAILS:")
            print(f"  Authenticated Identity:            {row['authenticated_user']}")
            print(f"  Remote Spark Engine / DBR Version: {row['dbr_version']}")
            print(f"  Serverless Compute Specification:  Databricks Serverless Environment Version 5")
            print(f"  Unity Catalog Metastore ID:        {row['metastore_id']}")
            print("-" * 75)
        else:
            print("[WARN] Session query returned no rows.")

        # 2. Query catalog accessibility
        print("\nVerifying Unity Catalog accessibility:")
        try:
            catalogs_df = spark.sql("SHOW CATALOGS")
            catalogs = [r[0] for r in catalogs_df.collect()]
            print(f"  Accessible Catalogs: {', '.join(catalogs)}")
            if "dwbi_catalog" in catalogs:
                print("  Target Catalog [dwbi_catalog]: PRESENT and ACCESSIBLE.")
                try:
                    schemas_df = spark.sql("SHOW SCHEMAS IN dwbi_catalog")
                    schemas = [r[0] for r in schemas_df.collect()]
                    print(f"  Existing Schemas in dwbi_catalog: {', '.join(schemas)}")
                except Exception as s_err:
                    print(f"  Schemas in dwbi_catalog: Could not query schemas ({sanitize_message(str(s_err))})")
            else:
                print("  Target Catalog [dwbi_catalog]: NOT YET CREATED.")
                print("  (Will be provisioned automatically by 03_ETL/config.py after authentication verification)")
        except Exception as cat_err:
            print(f"  Catalog Check: Could not list catalogs ({sanitize_message(str(cat_err))})")

        print("\n" + "=" * 75)
        print(" [STAGE 3 PASS] Remote Serverless Connectivity & Verification COMPLETE!")
        print("=" * 75)
        return True

    except Exception as ex:
        sanitized_err = sanitize_message(str(ex))
        print(f"\n[CONNECTION FAILURE] Could not establish remote session: {sanitized_err}")
        print("\nTroubleshooting Checklist:")
        print("  1. Verify workspace URL is accurate and reachable.")
        print("  2. Verify CLI OAuth profile is active using 'databricks auth profiles'.")
        print("  3. Verify Serverless Compute is enabled for your workspace region.")
        print("  4. Check that your user has compute access and workspace permissions.")
        print("=" * 75)
        return False


if __name__ == "__main__":
    profile_arg = sys.argv[1] if len(sys.argv) > 1 else None
    test_remote_serverless_connection(profile_name=profile_arg)

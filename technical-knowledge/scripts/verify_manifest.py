#!/usr/bin/env python3
"""
Integrity verification script for technical-knowledge documents.
Verifies byte-level integrity against technical-knowledge/manifest.json.
Avoids loading full document contents into model context during routine integrity checks.

Does NOT verify semantic correctness.
Never automatically accepts a new baseline without explicit invocation (--rebaseline).
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = KNOWLEDGE_DIR / "manifest.json"

# Strict exclusion list: Excluded from manifest integrity tracking
EXCLUDED_FILES = {
    "manifest.json",
    "SESSION_CONTEXT.md",
}
EXCLUDED_DIRS = {
    "scripts",
    "__pycache__",
}


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def discover_source_documents(knowledge_dir: Path) -> dict[str, Path]:
    documents = {}
    for item in knowledge_dir.iterdir():
        if item.is_dir() and item.name in EXCLUDED_DIRS:
            continue
        if item.is_file() and item.suffix.lower() == ".md" and item.name not in EXCLUDED_FILES:
            documents[item.name] = item
    return documents


def verify_manifest(rebaseline: bool = False) -> int:
    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Manifest file not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse manifest JSON: {e}", file=sys.stderr)
        return 1

    tracked_docs = manifest.get("documents", {})
    actual_docs = discover_source_documents(KNOWLEDGE_DIR)

    modified = []
    added = []
    deleted = []
    unchanged = []

    # Check tracked files for modifications or deletions
    for doc_name, meta in tracked_docs.items():
        doc_path = KNOWLEDGE_DIR / doc_name
        if not doc_path.exists():
            deleted.append(doc_name)
        else:
            current_hash = compute_sha256(doc_path)
            expected_hash = meta.get("sha256", "").lower()
            if current_hash == expected_hash:
                unchanged.append(doc_name)
            else:
                modified.append((doc_name, expected_hash[:12], current_hash[:12]))

    # Check for newly added documents not tracked in manifest
    for doc_name in actual_docs:
        if doc_name not in tracked_docs:
            added.append(doc_name)

    print("==================================================================")
    print(" KNOWLEDGE BASE INTEGRITY VERIFICATION REPORT (SHA-256)")
    print("==================================================================")
    print(f"Target Directory: {KNOWLEDGE_DIR}")
    print(f"Tracked Baseline Documents: {len(tracked_docs)}")
    print(f"Unchanged Documents:       {len(unchanged)}")

    has_discrepancy = bool(modified or added or deleted)

    if unchanged:
        for name in sorted(unchanged):
            print(f"  [OK]       {name}")

    if modified:
        print("\n[MODIFIED DOCUMENTS] (Byte changes detected on disk):")
        for name, exp, curr in modified:
            print(f"  ! {name} (expected {exp}..., found {curr}...)")

    if added:
        print("\n[ADDED DOCUMENTS] (Untracked files discovered in knowledge dir):")
        for name in added:
            print(f"  + {name}")

    if deleted:
        print("\n[DELETED / MISSING DOCUMENTS] (Tracked files missing from disk):")
        for name in deleted:
            print(f"  - {name}")

    print("------------------------------------------------------------------")

    if not has_discrepancy:
        print("[SUCCESS] All Layer 2 authoritative documents match verified baseline hashes.")
        print("          Safe to load Layer 1 SESSION_CONTEXT.md without reading full documents.")
        return 0

    if rebaseline:
        print("\n[REBASELINE] Updating manifest with current file hashes as requested...")
        new_manifest_docs = {}
        for name, path in actual_docs.items():
            new_manifest_docs[name] = {
                "sha256": compute_sha256(path),
                "bytes": path.stat().st_size,
                "purpose": tracked_docs.get(name, {}).get("purpose", "Authoritative knowledge document")
            }
        manifest["documents"] = new_manifest_docs
        manifest["last_verified"] = "MANUAL_REBASELINE"
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print("[SUCCESS] manifest.json successfully re-baselined.")
        return 0

    print("[ACTION REQUIRED] Integrity discrepancies detected!")
    print("                  1. Inspect git diff / changes before accepting any new baseline.")
    print("                  2. Update SESSION_CONTEXT.md ONLY if semantic understanding changes.")
    print("                  3. Run 'python verify_manifest.py --rebaseline' to update the manifest.")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify knowledge base SHA-256 manifest.")
    parser.add_argument("--rebaseline", action="store_true", help="Explicitly update manifest baseline with current file hashes after inspection.")
    args = parser.parse_args()
    sys.exit(verify_manifest(rebaseline=args.rebaseline))


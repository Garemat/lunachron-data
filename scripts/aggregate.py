#!/usr/bin/env python3
"""
Aggregate individual JSON files into a single build/compendium.json artifact.

In CI the version comes from the COMPENDIUM_VERSION env var (set from the release
tag by publish-release.yml).

For local development runs the script reads the latest git tag and increments the
patch version by 1 (e.g. v0.0.2 → 0.0.3).  This means a locally-built compendium
is always newer than the last published release, so the app won't prompt for an
update when using a dev build.

Usage:
    python3 scripts/aggregate.py
    python3 scripts/lint_data.py
"""

import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT, "build")

SOURCES = [
    ("characters", "characters/**/*.json"),
    ("upgrades",   "upgrades/**/*.json"),
    ("campaign",   "campaign/**/*.json"),
    ("rules",      "rules/**/*.json"),
]


def next_local_version():
    """Return latest git tag with patch bumped by 1, e.g. v0.0.2 -> 0.0.3."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=ROOT
        )
        if result.returncode == 0:
            tag = result.stdout.strip().lstrip("v")
            parts = tag.split(".")
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                return ".".join(parts)
    except Exception:
        pass
    return "0.0.1"


def aggregate():
    version = os.environ.get("COMPENDIUM_VERSION") or next_local_version()
    os.makedirs(BUILD_DIR, exist_ok=True)
    ok = True
    compendium = {"version": version}

    for kind, pattern in SOURCES:
        files = sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True))
        if not files:
            print(f"WARNING: no files matched {pattern}", file=sys.stderr)
            ok = False
            compendium[kind] = []
            continue

        entries = []
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    entries.append(json.load(f))
            except json.JSONDecodeError as e:
                print(f"ERROR: invalid JSON in {os.path.relpath(path, ROOT)}: {e}", file=sys.stderr)
                ok = False

        compendium[kind] = entries
        print(f"  {kind}: {len(entries)} entries")

    out_path = os.path.join(BUILD_DIR, "compendium.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(compendium, f, indent=2)
    print(f"  version: {version} -> build/compendium.json")

    return ok


if __name__ == "__main__":
    print("Aggregating JSON data...")
    if aggregate():
        print("Done. Run 'python3 scripts/lint_data.py' to validate.")
    else:
        sys.exit(1)

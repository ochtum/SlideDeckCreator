#!/usr/bin/env python3
"""Run independent skill test suites in separate processes to avoid import clashes."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
failed = []
for folder in sorted((ROOT / ".codex/skills").glob("*/scripts")):
    if not list(folder.glob("test_*.py")):
        continue
    result = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", str(folder), "-p", "test_*.py"], cwd=ROOT)
    if result.returncode:
        failed.append(str(folder.relative_to(ROOT)))
result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/sync_skills.py")], cwd=ROOT)
if result.returncode:
    failed.append("skill copy consistency")
if failed:
    print("FAILED: " + ", ".join(failed))
    raise SystemExit(1)
print("OK: all Python suites and skill copy consistency")

#!/usr/bin/env python3
"""Deprecated compatibility wrapper. Use `modernize validate`."""
from pathlib import Path
import subprocess, sys
HERE = Path(__file__).resolve().parent
print("WARN: validate_migration_state.py is deprecated; use `python scripts/modernize.py validate --repo <repo>`")
repo = sys.argv[1] if len(sys.argv) > 1 else "."
raise SystemExit(subprocess.call([sys.executable, str(HERE / "validate_governance.py"), repo]))

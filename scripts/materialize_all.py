"""
Headless materialization script for Dagster assets.

This script runs the full pipeline end-to-end without requiring the Dagster UI
or dev server to be running. It's designed to be called from GitHub Actions
or other automation.

Usage:
    python scripts/materialize_all.py
"""

import sys
import pathlib
import subprocess
import platform

PROJECT_ROOT = pathlib.Path(__file__).parent.parent

# Platform-agnostic venv Python path
if platform.system() == "Windows":
    VENV_PYTHON = pathlib.Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
    DBT_EXEC = pathlib.Path(__file__).parent.parent / ".venv" / "Scripts" / "dbt.exe"
else:
    VENV_PYTHON = pathlib.Path(__file__).parent.parent / ".venv" / "bin" / "python"
    DBT_EXEC = pathlib.Path(__file__).parent.parent / ".venv" / "bin" / "dbt"

print("=== Running World Bank ingestion ===")
result = subprocess.run(
    [str(VENV_PYTHON), "ingestion/run_worldbank.py"],
    cwd=str(PROJECT_ROOT),
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"World Bank ingestion failed: {result.stderr}")
    sys.exit(1)
print(result.stdout)

print("=== Running PSA CPI ingestion ===")
result = subprocess.run(
    [str(VENV_PYTHON), "ingestion/run_psa_cpi.py"],
    cwd=str(PROJECT_ROOT),
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"PSA CPI ingestion failed: {result.stderr}")
    sys.exit(1)
print(result.stdout)

print("=== Running dbt transformations ===")
result = subprocess.run(
    [str(DBT_EXEC), "run", "--profiles-dir=."],
    cwd=str(PROJECT_ROOT / "transform"),
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"dbt run failed: {result.stderr}")
    sys.exit(1)
print(result.stdout)

print("=== Running JSON export ===")
result = subprocess.run(
    [str(VENV_PYTHON), "export/build_export.py"],
    cwd=str(PROJECT_ROOT),
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"JSON export failed: {result.stderr}")
    sys.exit(1)
print(result.stdout)

print("=== All steps completed successfully ===")

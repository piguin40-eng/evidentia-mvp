from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    ROOT / "deploy_assets/bootstrap_model.joblib",
    ROOT / "deploy_assets/model_benchmark.json",
    ROOT / "deploy_assets/seed_manifest.json",
    ROOT / "deploy_assets/synthetic_dental_arch.stl",
    ROOT / "deploy_assets/knowledge.db",
)


@pytest.fixture(scope="session", autouse=True)
def ensure_synthetic_bootstrap_assets() -> None:
    if all(path.is_file() for path in REQUIRED):
        return
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_bootstrap_assets.py")],
        cwd=ROOT,
        check=True,
    )
    missing = [str(path) for path in REQUIRED if not path.is_file()]
    if missing:
        raise RuntimeError(f"El generador no creó los activos sintéticos: {missing}")

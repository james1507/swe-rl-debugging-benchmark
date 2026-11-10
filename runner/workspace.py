"""Task registry, isolated workspace copies and content fingerprints."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "01": "01-broken-banking-api",
    "02": "02-broken-ci-pipeline",
    "03": "03-duplicate-transactions",
}
IGNORED = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", ".pytest_cache", "*.pyc", "dist", "build", "artifacts",
)


def copy_workspace(source: Path, destination: Path, task: Path) -> None:
    """Copy without following links; build/dependency inputs belong to evaluator."""
    shutil.copytree(source, destination, symlinks=True, ignore=IGNORED)
    if any(path.is_symlink() for path in destination.rglob("*")):
        raise ValueError("workspace must not contain symbolic links")
    shutil.copy2(ROOT / "requirements.txt", destination / "requirements.txt")
    shutil.copy2(task / "environment" / "Dockerfile", destination / "Dockerfile")


def fingerprint(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(workspace.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(workspace).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()



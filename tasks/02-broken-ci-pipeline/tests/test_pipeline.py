import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path.cwd()


@pytest.fixture
def scratch_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    shutil.copytree(ROOT, workspace, ignore=shutil.ignore_patterns("dist", "__pycache__", ".pytest_cache"))
    return workspace


def run_pipeline(root=ROOT, **env_overrides):
    env = os.environ.copy()
    env.update(env_overrides)
    return subprocess.run(
        ["bash", "ci.sh"], cwd=root, env=env, text=True, capture_output=True, timeout=30,
    )


def test_workflow_runs_correct_script():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["build"]["steps"]
    commands = [step.get("run", "") for step in steps]
    assert any("python -m pip install pytest" in command for command in commands)
    assert any("bash ci.sh" in command for command in commands)
    assert not any("bash build.sh" in command for command in commands)
    assert any(step.get("uses", "").startswith("actions/setup-python@") for step in steps)


def test_ci_pipeline_produces_valid_artifact():
    source = ROOT / "src/calc.py"
    original = source.read_bytes()
    result = run_pipeline()
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((ROOT / "dist/build_manifest.json").read_text())
    assert manifest == {"source": "src/calc.py", "sha256": hashlib.sha256(original).hexdigest()}
    assert source.read_bytes() == original


def test_repeated_build_is_byte_identical():
    first = run_pipeline(PYTHONHASHSEED="1")
    assert first.returncode == 0, first.stdout + first.stderr
    output = ROOT / "dist/build_manifest.json"
    expected = output.read_bytes()
    output.unlink()
    second = run_pipeline(PYTHONHASHSEED="42")
    assert second.returncode == 0, second.stdout + second.stderr
    assert output.read_bytes() == expected


def test_failing_unit_test_blocks_build(scratch_workspace):
    workspace = scratch_workspace
    (workspace / "tests/test_forced_failure.py").write_text(
        "def test_forced_failure():\n    assert False, 'unit tests must gate the build'\n",
        encoding="utf-8",
    )
    result = run_pipeline(workspace)
    assert result.returncode != 0
    assert "unit tests must gate the build" in result.stdout + result.stderr
    assert not (workspace / "dist/build_manifest.json").exists()


def test_compile_error_blocks_build(scratch_workspace):
    (scratch_workspace / "src/broken.py").write_text("def broken(:\n", encoding="utf-8")
    result = run_pipeline(scratch_workspace)
    assert result.returncode != 0
    assert "broken.py" in result.stdout + result.stderr
    assert not (scratch_workspace / "dist/build_manifest.json").exists()


def test_manifest_tracks_changed_source(scratch_workspace):
    source = scratch_workspace / "src/calc.py"
    source.write_bytes(source.read_bytes() + b"\n# changed source bytes\n")
    result = run_pipeline(scratch_workspace)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((scratch_workspace / "dist/build_manifest.json").read_text())
    assert manifest["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (-2, 3, 1), (0, 0, 0), (10**30, 1, 10**30 + 1)])
def test_calculator_behavior_unchanged(a, b, expected):
    result = subprocess.run(
        [sys.executable, "-c", "from src.calc import add; import sys; print(add(int(sys.argv[1]), int(sys.argv[2])))", str(a), str(b)],
        cwd=ROOT, text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert int(result.stdout.strip()) == expected

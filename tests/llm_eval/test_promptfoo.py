import importlib.util
import shutil
import subprocess
from pathlib import Path
import pytest


def test_promptfoo_runs():
    if not shutil.which('promptfoo') or importlib.util.find_spec('promptfoo') is None:
        pytest.skip('promptfoo not installed')
    result = subprocess.run(
        ['promptfoo', 'test', str(Path(__file__).resolve().parents[2] / 'promptfoo.yaml')],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

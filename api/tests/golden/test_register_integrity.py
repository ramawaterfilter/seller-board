import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("script,expected", [
    ("engineering/check_register.py", "155 golden vectors"),
    ("engineering/reference_calcs.py", "155/155 vectors pass"),
])
def test_engineering_baseline(script, expected):
    result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / script)],
                            cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                            capture_output=True, text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert expected in result.stdout


def test_agent_instructions_match_template():
    assert (ROOT / "AGENTS.md").read_bytes() == (ROOT / "prompts/AGENTS.md").read_bytes()

"""The skills tell Copilot agents how to edit AI-safe workbooks with plain openpyxl.

This test runs the worked example from the Excel Expert skill in an isolated Python
(-I, so it cannot import the engine) and checks the engine accepts the result. If the
format or the skill text drifts apart, this fails.
"""

import json
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

from adlc_workbook import AdlcWorkbook, validate_workbook

from paths import SKILLS  # noqa: E402

EXAMPLE = SKILLS / "excel-expert" / "references" / "apply_change_example.py"


def test_agent_style_edit_is_accepted_by_the_engine(built, tmp_path):
    src = built("action-tracker")
    dst = tmp_path / "changed.xlsx"
    out = subprocess.run([sys.executable, "-I", str(EXAMPLE), str(src), str(dst)],
                         capture_output=True, text=True, check=True, cwd=tmp_path)
    result = json.loads(out.stdout)
    assert result["version"] == "1.1" and result["new_id"] == "ACT-002"
    assert all(c.startswith("Actions!") for c in result["changed"]), result["changed"]

    report = validate_workbook(load_workbook(dst))
    assert report.ok, report.text()
    awb = AdlcWorkbook.open(dst)
    assert awb.meta["integrity"] == "ok"
    assert awb.meta["version"] == "1.1"

    # ...and the engine can carry on from the agent's edit.
    awb.apply([{"op": "update_rows", "table": "actions", "id": "ACT-002", "set": {"Priority": "High"}}],
              requested_by="pytest")
    awb.save()
    assert validate_workbook(load_workbook(dst)).ok

"""Produce a set of workbooks changed by the engines, for checking in real Excel.

    python tools/engine_smoke.py OUT_DIR
    powershell -File tools/excel_check.ps1 OUT_DIR/*.xlsx

Every file must open without a repair prompt and without #REF!/#NAME? errors.
Uses only synthetic data.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import BUILD, SRC, TEMPLATE_WORKBOOKS, TESTS  # noqa: E402

sys.path[:0] = [str(SRC), str(TESTS)]

from adlc_excel import ExpertWorkbook  # noqa: E402
from adlc_pii.scrub import restore_file, scrub_file  # noqa: E402
from adlc_workbook import AdlcWorkbook, load_spec  # noqa: E402
from fixtures_excel import make_claims_workbook  # noqa: E402


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    base = make_claims_workbook(out / "00 claims (original).xlsx")

    scenarios = {
        "01 insert column": [{"op": "insert_column", "sheet": "Claims", "header": "Priority", "after": "Team",
                              "choices": ["High", "Medium", "Low"], "fill": "Medium"}],
        "02 add rows + move totals": [{"op": "add_rows", "sheet": "Claims", "rows": [
            {"Member": f"PERSON_1{i}", "Team": "Dental", "Received": "2026-09-2" + str(i), "Amount": 10 * i, "Status": "Open"}
            for i in range(1, 4)]}],
        "03 delete, sort, dedupe": [{"op": "dedupe", "sheet": "Claims", "columns": ["Ref"]},
                                    {"op": "delete_rows", "sheet": "Claims", "where": {"Status": "Pending"}},
                                    {"op": "sort", "sheet": "Claims", "by": [{"column": "Amount", "order": "desc"}]}],
        "04 lookup, summary, highlight": [
            {"op": "add_lookup_column", "sheet": "Claims", "header": "Manager", "key_column": "Team",
             "from": {"sheet": "Teams", "key_column": "Team", "return_column": "Manager"}},
            {"op": "add_summary", "sheet": "Claims", "group_by": "Team",
             "measures": [{"agg": "count"}, {"agg": "sum", "column": "Amount", "number_format": "currency"},
                          {"agg": "max", "column": "Amount"}], "chart": "column"},
            {"op": "conditional_format", "sheet": "Claims", "column": "Amount", "rule": "color_scale"},
            {"op": "conditional_format", "sheet": "Claims", "column": "Status", "rule": "equals", "value": "Open",
             "color": "amber", "whole_row": True}],
        "05 table, rename, split": [
            {"op": "convert_to_table", "sheet": "Teams"},
            {"op": "insert_column", "table": "tblTeams", "header": "Budget incl VAT", "formula": "=[@Budget]*1.23",
             "number_format": "currency"},
            {"op": "rename_column", "table": "tblTeams", "column": "Budget", "new_header": "Annual budget"},
            {"op": "rename_sheet", "sheet": "Claims", "new_name": "Claims 2026"},
            {"op": "add_validation", "sheet": "Claims 2026", "column": "Amount", "kind": "decimal", "min": 0, "max": 100000}],
    }
    for name, ops in scenarios.items():
        xw = ExpertWorkbook.open(base)
        res = xw.apply(ops, requested_by="smoke")
        xw.save(out / f"{name}.xlsx")
        print(f"{name}: {len(res.changes)} change(s)")

    tracker = AdlcWorkbook.build(load_spec(TEMPLATE_WORKBOOKS / "action-tracker.spec.yaml"))
    tracker.save(out / "06 action tracker.xlsx")
    xw = ExpertWorkbook.open(out / "06 action tracker.xlsx")
    xw.apply([{"op": "insert_column", "table": "tblActions", "header": "Priority", "after": "Status", "choices": ["High", "Low"]},
              {"op": "add_rows", "table": "tblActions", "rows": [{"Action": "Book room", "Owner": "Aoife", "Priority": "High"}]},
              {"op": "add_summary", "table": "tblActions", "group_by": "Owner"}], requested_by="smoke")
    xw.save(out / "06 action tracker (expert edit, AI-safe).xlsx")
    print("06 AI-safe workbook edited, version", AdlcWorkbook.open(out / "06 action tracker (expert edit, AI-safe).xlsx").meta["version"])

    clean, report, vault = scrub_file(base, out / "07 claims (PII removed).xlsx")
    restore_file(clean, vault, out / "07 claims (restored).xlsx")
    print("07 PII clean + restore")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else BUILD / "engine-smoke"))

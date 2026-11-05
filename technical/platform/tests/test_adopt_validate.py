from datetime import datetime

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from adlc_workbook import AdlcWorkbook, DriftError, adopt, validate_workbook


@pytest.fixture
def legacy(tmp_path):
    """An ordinary workbook someone made by hand: plain range, a formula column, a totals row."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Claims Queue"
    ws.append(["Case", "Received", "Team", "Amount", "Days open"])
    teams = ["Hospital", "Outpatient", "Hospital", "Dental", "Hospital", "Outpatient"]
    for i, team in enumerate(teams, start=2):
        ws.append([f"Case {i}", datetime(2026, 9, i), team, 100 * i, f"=TODAY()-B{i}"])
    ws.append(["Total", None, None, "=SUM(D2:D7)", None])
    dv = DataValidation(type="list", formula1='"Hospital,Outpatient,Dental"')
    dv.add("C2:C100")
    ws.add_data_validation(dv)
    path = tmp_path / "legacy.xlsx"
    wb.save(path)
    return path


def test_adopt_dry_run_infers_types(legacy):
    res = adopt(legacy, write=False)
    cols = {c["header"]: c for c in res.spec["sheets"][0]["tables"][0]["columns"]}
    assert cols["Received"]["type"] == "date"
    assert cols["Team"]["type"] == "choice" and cols["Team"]["choices"] == ["Hospital", "Outpatient", "Dental"]
    assert cols["Amount"]["type"] == "integer"
    assert cols["Days open"]["type"] == "formula" and cols["Days open"]["formula_a1"] == "=TODAY()-B2"
    assert cols["ID"]["type"] == "id"
    assert any("totals row" in n for n in res.notes)


def test_adopt_then_change(legacy, tmp_path):
    res = adopt(legacy, title="Claims queue")
    out = res.awb.save(tmp_path / "adopted.xlsx")
    ws = load_workbook(out)["Claims Queue"]
    assert ws["F1"].value == "ID" and ws["F2"].value == "CLA-001" and ws["F7"].value == "CLA-006"
    assert ws["A8"].value == "Total" and ws["D8"].value == "=SUM(D2:D7)"
    assert validate_workbook(load_workbook(out)).ok

    new_row = [{"op": "add_rows", "table": "claims_queue", "rows": [
        {"Case": "Case 9", "Received": "01/10/2026", "Team": "Dental", "Amount": 50}]}]
    # The totals row sits right under the table, so growing it would overwrite the total.
    awb = AdlcWorkbook.open(out)
    with pytest.raises(DriftError, match="A8"):
        awb.apply(new_row, requested_by="pytest")
    assert load_workbook(out)["Claims Queue"]["D8"].value == "=SUM(D2:D7)"

    # Once the person moves the totals row away, the change goes through.
    wb = load_workbook(out)
    ws = wb["Claims Queue"]
    ws["A8"], ws["D8"] = None, None
    ws["A12"], ws["D12"] = "Total", "=SUM(tblClaimsQueue[Amount])"
    wb.save(out)
    awb = AdlcWorkbook.open(out)
    awb.apply(new_row, requested_by="pytest")
    awb.save()
    ws = load_workbook(out)["Claims Queue"]
    assert ws["E8"].value == "=TODAY()-B8"
    assert ws["F8"].value == "CLA-007"
    assert ws["A12"].value == "Total"


def test_adopt_refuses_adlc_workbooks(built):
    with pytest.raises(ValueError, match="already an ADLC"):
        adopt(built("simple-register"))


def test_validate_spots_drift(built):
    path = built("action-tracker")
    wb = load_workbook(path)
    ws = wb["Actions"]
    ws["I2"] = 99                 # typed over a formula
    ws["C1"] = "Person"           # header renamed by hand
    wb.save(path)
    rep = validate_workbook(load_workbook(path))
    assert not rep.ok
    assert any("don't match the spec" in e for e in rep.errors)

    wb = load_workbook(path)
    wb["Actions"]["C1"] = "Owner"
    wb.save(path)
    rep = validate_workbook(load_workbook(path))
    assert any("should be calculated" in e for e in rep.errors)


def test_validate_spots_duplicate_ids_and_blank_required(built):
    path = built("action-tracker")
    awb = AdlcWorkbook.open(path)
    awb.apply([{"op": "add_rows", "table": "actions", "rows": [{"Action": "No owner"}]}], requested_by="pytest")
    awb.save()
    wb = load_workbook(path)
    wb["Actions"]["A3"] = "ACT-001"
    wb.save(path)
    rep = validate_workbook(load_workbook(path))
    assert any("Duplicate IDs" in e for e in rep.errors)
    assert any("missing 'Owner'" in w for w in rep.warnings)


def test_agent_written_spec_with_shorthand_formulas_is_accepted(built):
    """Copilot agents write _ADLC themselves: shorthand formulas and missing defaults must not look like drift."""
    import json

    from adlc_workbook.meta import META_SHEET

    path = built("action-tracker")
    wb = load_workbook(path)
    ws = wb[META_SHEET]
    for row in ws.iter_rows(min_row=2):
        if row[0].value == "spec_1":
            spec = json.loads(row[1].value)
            table = spec["sheets"][0]["tables"][0]
            for col in table["columns"]:
                col.pop("description", None)
                col.pop("required", None)
                if col["key"] == "days_left":
                    col["formula"] = '=IF(OR([@[Due date]]="",[@Status]="Done"),"",[@[Due date]]-TODAY())'
            table.pop("anchor", None)
            row[1].value = json.dumps(spec)
    wb.save(path)

    rep = validate_workbook(load_workbook(path))
    assert rep.ok, rep.text()
    awb = AdlcWorkbook.open(path)
    awb.apply([{"op": "add_rows", "table": "actions", "rows": [{"Action": "From an agent-built file"}]}],
              requested_by="pytest")
    awb.save()
    assert validate_workbook(load_workbook(path)).ok

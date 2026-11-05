import json

import pytest
from openpyxl import load_workbook

from adlc_workbook import AdlcWorkbook, MetaError, SpecError, load_spec, prepare_spec, read_meta
from adlc_workbook.meta import META_SHEET, spec_hash

TEMPLATES = ["action-tracker", "raid-log", "project-plan", "simple-register"]


@pytest.mark.parametrize("name", TEMPLATES)
def test_every_template_builds_and_validates(built, name):
    path = built(name)
    awb = AdlcWorkbook.open(path)
    report = awb.validate()
    assert report.ok, report.text()
    assert awb.meta["version"] == "1.0"


@pytest.mark.parametrize("name", TEMPLATES)
def test_meta_round_trip_keeps_spec_without_seed_rows(built, spec_path, name):
    path = built(name)
    meta, spec = read_meta(load_workbook(path))
    original = load_spec(spec_path(name))
    assert spec["workbook"]["title"] == original["workbook"]["title"]
    assert all("rows" not in t for s in spec["sheets"] for t in s["tables"])
    assert [s["name"] for s in spec["sheets"]] == [s["name"] for s in original["sheets"]]
    assert meta["workbook_id"]


def test_sheet_order_and_visibility(built):
    wb = load_workbook(built("action-tracker"))
    assert wb.sheetnames == ["README", "Actions", "Dashboard", "Settings", "Change Log", "_ADLC"]
    assert wb[META_SHEET].sheet_state == "hidden"
    assert wb.active.title == "README"
    assert sum(ws.sheet_view.tabSelected for ws in wb.worksheets) == 1


def test_formulas_are_written_in_file_form(built):
    wb = load_workbook(built("action-tracker"))
    ws = wb["Actions"]
    headers = [c.value for c in ws[1]]
    days_left = ws.cell(2, headers.index("Days left") + 1).value
    assert days_left.startswith("=IF(OR(tblActions[[#This Row],[Due date]]")
    assert "[@" not in days_left


def test_readme_never_contains_live_formulas(built):
    """A formula shown as help text must be stored as text, or Excel refuses the file."""
    wb = load_workbook(built("action-tracker"))
    for row in wb["README"].iter_rows():
        for cell in row:
            assert not (cell.data_type == "f"), f"README cell {cell.coordinate} is a formula"


def test_dropdowns_and_settings_names(built):
    wb = load_workbook(built("action-tracker"))
    ws = wb["Actions"]
    lists = [dv.formula1 for dv in ws.data_validations.dataValidation if dv.type == "list"]
    assert '"Not started,In progress,Blocked,Done"' in lists
    assert "p_due_soon_days" in wb.defined_names


def test_seed_rows_get_ids(built):
    ws = load_workbook(built("action-tracker"))["Actions"]
    assert ws["A2"].value == "ACT-001"


def test_long_choice_lists_use_hidden_lists_sheet(tmp_path):
    choices = [f"Department number {i}, Dublin" for i in range(30)]
    spec = {
        "workbook": {"title": "Long list"},
        "sheets": [{"name": "Data", "tables": [{"key": "data", "columns": [
            {"header": "Department", "type": "choice", "choices": choices}]}]}],
    }
    awb = AdlcWorkbook.build(spec)
    path = awb.save(tmp_path / "long.xlsx")
    wb = load_workbook(path)
    assert wb["_Lists"].sheet_state == "hidden"
    assert "lst_data_department" in wb.defined_names
    assert any(dv.formula1 == "=lst_data_department" for dv in wb["Data"].data_validations.dataValidation)


def test_invalid_spec_is_rejected_with_reasons():
    with pytest.raises(SpecError) as exc:
        prepare_spec({"workbook": {"title": "Bad"}, "sheets": [{"name": "README", "tables": [
            {"key": "t", "columns": [{"header": "A[1]"}, {"header": "Calc", "type": "formula"}]}]}]})
    text = str(exc.value)
    assert "reserved" in text and "must not be blank or contain" in text and "needs a formula" in text


def test_dynamic_array_formula_rejected():
    with pytest.raises(SpecError):
        prepare_spec({"workbook": {"title": "x"}, "sheets": [{"name": "S", "tables": [{"key": "t", "columns": [
            {"header": "Calc", "type": "formula", "formula": "=UNIQUE(tblT[ID])"}]}]}]})


def test_tampered_meta_is_detected(built):
    path = built("simple-register")
    wb = load_workbook(path)
    ws = wb[META_SHEET]
    for row in ws.iter_rows(min_row=2):
        if row[0].value == "spec_1":
            spec = json.loads(row[1].value)
            spec["workbook"]["title"] = "Hacked"
            row[1].value = json.dumps(spec)
    wb.save(path)
    awb = AdlcWorkbook.open(path)            # still opens, so nobody is locked out
    assert awb.meta["integrity"] == "mismatch"
    assert any("checksum" in w for w in awb.validate().warnings)


def test_missing_meta_sheet_is_reported(built):
    path = built("simple-register")
    wb = load_workbook(path)
    del wb[META_SHEET]
    wb.save(path)
    with pytest.raises(MetaError):
        AdlcWorkbook.open(path)


def test_spec_hash_is_stable():
    assert spec_hash({"b": 1, "a": [1, 2]}) == spec_hash({"a": [1, 2], "b": 1})

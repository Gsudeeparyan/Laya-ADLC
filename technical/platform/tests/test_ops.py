from datetime import datetime

import pytest
from openpyxl import load_workbook

from adlc_workbook import AdlcWorkbook, OpError, diff_files
from adlc_workbook.diff import snapshot


def headers(ws):
    return [c.value for c in ws[1] if c.value is not None]


def change(path, ops, **kw):
    awb = AdlcWorkbook.open(path)
    res = awb.apply(ops, requested_by="pytest", **kw)
    awb.save(path)
    return awb, res


def test_add_column_after_with_fill_existing(built):
    path = built("action-tracker")
    _, res = change(path, [{"op": "add_column", "table": "actions", "after": "status", "fill_existing": "Medium",
                            "column": {"header": "Priority", "type": "choice", "choices": ["High", "Medium", "Low"]}}])
    ws = load_workbook(path)["Actions"]
    h = headers(ws)
    assert h.index("Priority") == h.index("Status") + 1
    assert ws.cell(2, h.index("Priority") + 1).value == "Medium"
    assert res.version == "1.1"
    assert AdlcWorkbook.open(path).validate().ok


def test_only_the_changed_table_changes(built, tmp_path):
    path = built("project-plan")
    before = tmp_path / "before.xlsx"
    before.write_bytes(path.read_bytes())
    change(path, [{"op": "add_rows", "table": "tasks", "rows": [
        {"Task": "Write the training guide", "Owner": "Aoife", "Start": "13/10/2026", "End": "24/10/2026", "Status": "In progress"}]}])
    lines = diff_files(before, path)
    assert lines, "expected some changes"
    assert all(line.startswith("~ Tasks!") for line in lines), lines


def test_add_rows_assigns_ids_and_coerces_values(built):
    path = built("action-tracker")
    change(path, [{"op": "add_rows", "table": "actions", "rows": [
        {"Action": "Book room", "Owner": "Liam", "Due date": "31/10/2026", "status": "in progress"},
        {"action": "Send minutes", "owner": "Ann", "due_date": "2026-11-02", "status": "Done"}]}])
    ws = load_workbook(path)["Actions"]
    assert [ws.cell(r, 1).value for r in (2, 3, 4)] == ["ACT-001", "ACT-002", "ACT-003"]
    h = headers(ws)
    assert ws.cell(3, h.index("Due date") + 1).value == datetime(2026, 10, 31)
    assert ws.cell(3, h.index("Status") + 1).value == "In progress"


@pytest.mark.parametrize("row, message", [
    ({"Action": "x", "Status": "Finished"}, "not one of the choices"),
    ({"Action": "x", "Due date": "next week"}, "not a date"),
    ({"Action": "x", "Days left": 3}, "calculated automatically"),
    ({"Action": "x", "Colour": "red"}, "no column called"),
])
def test_add_rows_rejects_bad_input(built, row, message):
    path = built("action-tracker")
    with pytest.raises(OpError, match=message):
        change(path, [{"op": "add_rows", "table": "actions", "rows": [row]}])


def test_failed_change_leaves_file_untouched(built):
    path = built("action-tracker")
    original = path.read_bytes()
    awb = AdlcWorkbook.open(path)
    spec_before = awb.spec
    with pytest.raises(OpError):
        awb.apply([
            {"op": "add_column", "table": "actions", "column": {"header": "Priority"}},
            {"op": "update_rows", "table": "actions", "id": "ACT-999", "set": {"Status": "Done"}},
        ], requested_by="pytest")
    assert awb.spec is spec_before
    assert path.read_bytes() == original


def test_update_and_delete_rows(built):
    path = built("action-tracker")
    change(path, [{"op": "add_rows", "table": "actions", "rows": [{"Action": "A2"}, {"Action": "A3"}]}])
    change(path, [{"op": "update_rows", "table": "actions", "ids": ["ACT-002", "act-003"], "set": {"Owner": "Niamh"}},
                  {"op": "delete_rows", "table": "actions", "ids": ["ACT-001"]}])
    ws = load_workbook(path)["Actions"]
    assert ws["A2"].value == "ACT-002" and ws["C2"].value == "Niamh"
    assert ws["A3"].value == "ACT-003" and ws["A4"].value is None
    with pytest.raises(OpError, match="IDs can't be changed"):
        change(path, [{"op": "update_rows", "table": "actions", "id": "ACT-002", "set": {"ID": "X"}}])


def test_rename_updates_formulas_in_this_and_other_tables(built):
    path = built("action-tracker")
    change(path, [{"op": "rename_column", "table": "actions", "column": "Flag", "header": "Warning"},
                  {"op": "rename_column", "table": "actions", "column": "due_date", "header": "Deadline"}])
    awb = AdlcWorkbook.open(path)
    assert awb.validate().ok
    flag_users = [c["formula"] for s in awb.spec["sheets"] for t in s["tables"] for c in t["columns"] if c.get("formula")]
    assert not any("[Due date]" in f or "[Flag]" in f for f in flag_users)
    dash = load_workbook(path)["Dashboard"]
    assert "tblActions[Warning]" in dash["C2"].value


def test_remove_column_blocked_when_used(built):
    path = built("action-tracker")
    with pytest.raises(OpError, match="used by"):
        change(path, [{"op": "remove_column", "table": "actions", "column": "Due date"}])
    with pytest.raises(OpError, match="ID column"):
        change(path, [{"op": "remove_column", "table": "actions", "column": "ID"}])
    change(path, [{"op": "remove_column", "table": "actions", "column": "Notes"}])
    assert "Notes" not in headers(load_workbook(path)["Actions"])


def test_set_choices_protects_existing_values(built):
    path = built("action-tracker")
    with pytest.raises(OpError, match="still use"):
        change(path, [{"op": "set_choices", "table": "actions", "column": "Status",
                       "choices": ["Open", "Done"]}])
    change(path, [{"op": "set_choices", "table": "actions", "column": "Status", "choices": ["Cancelled"], "mode": "add"}])
    wb = load_workbook(path)
    lists = [dv.formula1 for dv in wb["Actions"].data_validations.dataValidation if dv.type == "list"]
    assert '"Not started,In progress,Blocked,Done,Cancelled"' in lists
    assert [wb["Dashboard"].cell(r, 1).value for r in range(2, 7)][-1] == "Cancelled"


def test_set_formula_needs_force_over_typed_values(built):
    path = built("action-tracker")
    with pytest.raises(OpError, match="typed value"):
        change(path, [{"op": "set_formula", "table": "actions", "column": "Owner", "formula": '="x"'}])
    change(path, [{"op": "set_formula", "table": "actions", "column": "Days left",
                   "formula": '=IF([@[Due date]]="","",NETWORKDAYS(TODAY(),[@[Due date]]))'}])
    assert "NETWORKDAYS" in load_workbook(path)["Actions"]["I2"].value


def test_set_parameter_and_new_parameter(built):
    path = built("action-tracker")
    change(path, [{"op": "set_parameter", "key": "due_soon_days", "value": "10"},
                  {"op": "set_parameter", "key": "team_size", "value": 8, "label": "People in the team"}])
    wb = load_workbook(path)
    assert wb["Settings"]["B2"].value == 10
    assert "p_team_size" in wb.defined_names


def test_settings_typed_in_excel_are_kept(built):
    path = built("action-tracker")
    wb = load_workbook(path)
    wb["Settings"]["B2"].value = 3
    wb.save(path)
    change(path, [{"op": "add_rows", "table": "actions", "rows": [{"Action": "x"}]}])
    assert load_workbook(path)["Settings"]["B2"].value == 3


def test_add_table_on_new_sheet(built):
    path = built("simple-register")
    change(path, [{"op": "add_table", "sheet": "Contacts", "sheet_description": "People to contact",
                   "table": {"key": "contacts", "columns": [{"header": "Name", "required": True}, {"header": "Email"}],
                             "rows": [{"Name": "Mary"}]}}])
    wb = load_workbook(path)
    assert wb.sheetnames.index("Contacts") < wb.sheetnames.index("Change Log")
    assert wb["Contacts"]["A2"].value == "CON-001"
    assert AdlcWorkbook.open(path).validate().ok


def test_charts_are_recreated_not_duplicated(built):
    path = built("raid-log")
    for i in range(3):
        change(path, [{"op": "add_rows", "table": "raid", "rows": [{"Type": "Issue", "Title": f"I{i}"}]}])
    wb = load_workbook(path)
    assert len(wb["Summary"]._charts) == 1


def test_chart_ops(built):
    path = built("action-tracker")
    change(path, [{"op": "add_chart", "sheet": "Dashboard", "chart": {
        "key": "overdue", "type": "bar", "title": "Overdue by status", "table": "status_summary",
        "category": "status", "values": ["overdue"], "anchor": "E20"}}])
    assert len(load_workbook(path)["Dashboard"]._charts) == 2
    change(path, [{"op": "remove_chart", "sheet": "Dashboard", "chart": "overdue"}])
    assert len(load_workbook(path)["Dashboard"]._charts) == 1


def test_change_log_and_version_history(built):
    path = built("simple-register")
    change(path, [{"op": "set_workbook_info", "title": "Supplier Register", "owner": "Procurement"}],
           summary="Renamed for suppliers")
    change(path, [{"op": "add_rows", "table": "register", "rows": [{"Item": "Acme Ltd"}]}])
    awb = AdlcWorkbook.open(path)
    assert awb.meta["version"] == "1.2" and awb.meta["owner"] == "Procurement"
    log = load_workbook(path)["Change Log"]
    assert [log.cell(r, 1).value for r in (2, 3, 4)] == ["1.0", "1.1", "1.2"]
    assert log.cell(3, 5).value == "Renamed for suppliers"
    assert load_workbook(path)["README"]["A1"].value == "Supplier Register"


def test_unknown_op_and_unknown_table(built):
    path = built("simple-register")
    with pytest.raises(OpError, match="unknown op"):
        change(path, [{"op": "explode"}])
    with pytest.raises(OpError, match="can't find a table"):
        change(path, [{"op": "add_rows", "table": "nope", "rows": []}])


def test_rows_typed_by_hand_in_excel_survive_a_change(built):
    """People add rows in Excel itself; the table grows and the engine keeps them."""
    path = built("action-tracker")
    wb = load_workbook(path)
    ws = wb["Actions"]
    t = ws.tables["tblActions"]
    ws["B3"], ws["C3"] = "Typed in Excel", "Sean"
    t.ref = t.autoFilter.ref = "A1:J3"
    wb.save(path)
    change(path, [{"op": "add_column", "table": "actions", "column": {"header": "Team"}}])
    ws = load_workbook(path)["Actions"]
    assert ws["A3"].value == "ACT-002" and ws["B3"].value == "Typed in Excel"
    snap = snapshot(load_workbook(path))["Actions"]
    assert snap["I3"].startswith("=IF(OR(tblActions")   # Days left formula filled in for the new row
    assert snap["K1"] == "Team"


def test_change_log_never_stores_row_values(built):
    path = built("action-tracker")
    change(path, [{"op": "add_rows", "table": "actions", "rows": [{"Action": "Call Mary Byrne on 087 123 4567"}]},
                  {"op": "update_rows", "table": "actions", "id": "ACT-001", "set": {"Owner": "Mary Byrne"}}])
    details = load_workbook(path)["Change Log"]["G3"].value
    assert "Mary" not in details and "087" not in details
    assert "values not logged" in details and "owner" in details.lower()

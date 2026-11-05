"""Expert Excel engine tests (any workbook, not just AI-safe ones)."""

import pytest
from openpyxl import load_workbook

from adlc_excel import ExpertWorkbook, OpError
from adlc_excel.refs import shift_address, shift_formula
from fixtures_excel import make_claims_workbook


@pytest.fixture
def claims(tmp_path):
    return make_claims_workbook(tmp_path / "claims.xlsx")


def apply(path, ops, out=None):
    xw = ExpertWorkbook.open(path)
    res = xw.apply(ops, requested_by="pytest")
    xw.save(out or path)
    return res, load_workbook(out or path)


# --------------------------------------------------------------------------- reference shifting


@pytest.mark.parametrize("formula, axis, at, n, expected", [
    ("=SUM(B2:D2)", "col", 3, 1, "=SUM(B2:E2)"),          # insert inside a range widens it
    ("=SUM(B2:D2)", "col", 2, 1, "=SUM(C2:E2)"),          # insert before shifts it
    ("=SUM(B2:D2)", "col", 5, 1, "=SUM(B2:D2)"),          # insert after leaves it
    ("=$E$2*2", "col", 1, 2, "=$G$2*2"),                  # absolute refs move too
    ("=C2+1", "col", 3, -1, "=#REF!+1"),                  # deleted cell -> #REF!
    ("=SUM(B2:D2)", "col", 3, -1, "=SUM(B2:C2)"),         # deleting inside shrinks
    ("=SUM(A2:A10)", "row", 5, 2, "=SUM(A2:A12)"),
    ("=Other!B2+B2", "col", 1, 1, "=Other!B2+C2"),        # only the target sheet moves
    ("=tblX[Amount]+B2", "col", 1, 1, "=tblX[Amount]+C2"),  # structured refs untouched
])
def test_shift_formula(formula, axis, at, n, expected):
    assert shift_formula(formula, "Data", "Data", axis, at, n) == expected


def test_shift_whole_columns_and_rows():
    assert shift_address("C:E", "col", 2, 1) == "D:F"
    assert shift_address("3:5", "row", 4, -1) == "3:4"


# --------------------------------------------------------------------------- columns


def test_insert_column_moves_everything_that_points_at_moved_cells(claims):
    res, wb = apply(claims, [{"op": "insert_column", "sheet": "Claims", "header": "Priority", "after": "Team",
                              "choices": ["High", "Medium", "Low"], "fill": "Medium"}])
    ws = wb["Claims"]
    assert [c.value for c in ws[1]][:8] == ["Ref", "Member", "Team", "Priority", "Received", "Amount", "Status", "VAT"]
    assert ws["H2"].value == "=F2*0.23" and ws["F9"].value == "=SUM(F2:F7)"
    assert wb["Report"]["B2"].value == '=SUMIFS(Claims!F2:F7,Claims!G2:G7,"Open")'
    assert wb["Report"]["B3"].value == "=MAX(Claims!$F$2:$F$7)"
    assert wb.defined_names["ClaimAmounts"].attr_text == "Claims!$F$2:$F$7"
    assert "J1:K1" in [str(m) for m in ws.merged_cells.ranges]
    sqrefs = {str(dv.sqref) for dv in ws.data_validations.dataValidation}
    assert "G2:G7" in sqrefs and "D2:D7" in sqrefs
    assert [str(cf.sqref) for cf in ws.conditional_formatting] == ["G2:G7"]
    assert wb["Report"]._charts[0].series[0].val.numRef.f.replace("$", "").replace("'", "") == "Claims!F2:F7"
    assert ws.column_dimensions["B"].width == 18
    assert ws["D2"].value == "Medium" and ws["D8"].value is None


def test_delete_column_refuses_when_formulas_would_break(claims):
    with pytest.raises(OpError, match="#REF!"):
        apply(claims, [{"op": "delete_column", "sheet": "Claims", "column": "Amount"}])
    res, wb = apply(claims, [{"op": "delete_column", "sheet": "Claims", "column": "Team"}])
    assert [c.value for c in wb["Claims"][1]][:3] == ["Ref", "Member", "Received"]
    assert wb["Claims"]["F2"].value == "=D2*0.23"


def test_rename_column_in_excel_table_updates_structured_refs(tmp_path, built):
    path = built("action-tracker")
    res, wb = apply(path, [{"op": "rename_column", "table": "tblActions", "column": "Due date", "new_header": "Deadline"}])
    assert "tblActions[[#This Row],[Deadline]]" in wb["Actions"]["I2"].value


# --------------------------------------------------------------------------- rows


def test_add_rows_extends_totals_and_fills_ids(claims):
    res, wb = apply(claims, [{"op": "add_rows", "sheet": "Claims", "rows": [
        {"Member": "PERSON_009", "Team": "Dental", "Received": "20/09/2026", "Amount": "€1,150.50", "Status": "open"}]}])
    ws = wb["Claims"]
    assert ws["A8"].value == "CLM-006"
    assert ws["E8"].value == 1150.5 and ws["D8"].value.day == 20 and ws["F8"].value == "Open"
    assert ws["G8"].value == "=E8*0.23"
    assert ws["E9"].value == "=SUM(E2:E8)"
    assert wb["Report"]["B3"].value == "=MAX(Claims!$E$2:$E$8)"
    assert wb.defined_names["ClaimAmounts"].attr_text == "Claims!$E$2:$E$8"
    assert any("F2:F8" in str(dv.sqref) for dv in ws.data_validations.dataValidation)


def test_add_rows_rejects_values_outside_dropdown_and_changes_nothing(claims):
    before = claims.read_bytes()
    with pytest.raises(OpError, match="isn't one of the options"):
        apply(claims, [{"op": "add_rows", "sheet": "Claims", "rows": [{"Member": "X", "Status": "Archived"}]}])
    assert claims.read_bytes() == before


def test_add_rows_moves_content_down_when_needed(claims):
    rows = [{"Member": f"PERSON_1{i}", "Amount": 10} for i in range(3)]
    res, wb = apply(claims, [{"op": "add_rows", "sheet": "Claims", "rows": rows}])
    ws = wb["Claims"]
    assert ws["A11"].value is None                      # the blank spacer row is kept
    assert ws["A12"].value == "Total" and ws["E12"].value == "=SUM(E2:E10)"
    assert wb["Report"]["B1"].value == "=Claims!E12"


def test_update_and_delete_where(claims):
    res, wb = apply(claims, [
        {"op": "update_rows", "sheet": "Claims", "where": [{"column": "Amount", "op": "greater_than", "value": 1000}],
         "set": {"Status": "Pending"}},
        {"op": "delete_rows", "sheet": "Claims", "where": {"Team": "Dental"}},
    ])
    ws = wb["Claims"]
    statuses = [ws.cell(r, 6).value for r in range(2, 7)]
    assert statuses.count("Pending") == 2
    assert "Dental" not in [ws.cell(r, 3).value for r in range(2, 8)]
    assert wb["Deleted rows"]["C2"].value == "CLM-004"
    assert ws["G5"].value == "=E5*0.23"   # formulas follow their rows
    with pytest.raises(OpError, match="No rows"):
        apply(claims, [{"op": "delete_rows", "sheet": "Claims", "where": {"Team": "Optical"}}])


def test_sort_and_dedupe(claims):
    res, wb = apply(claims, [{"op": "dedupe", "sheet": "Claims", "columns": ["Ref"]},
                             {"op": "sort", "sheet": "Claims", "by": [{"column": "Amount", "order": "desc"}]}])
    ws = wb["Claims"]
    amounts = [ws.cell(r, 5).value for r in range(2, 7)]
    assert amounts == sorted(amounts, reverse=True) and ws["A7"].value is None
    assert ws["G2"].value == "=E2*0.23" and ws["A2"].value == "CLM-005"
    assert wb["Removed duplicates"]["C2"].value == "CLM-002"


def test_lookup_summary_and_highlight(claims):
    res, wb = apply(claims, [
        {"op": "add_lookup_column", "sheet": "Claims", "header": "Manager", "key_column": "Team",
         "from": {"sheet": "Teams", "key_column": "Team", "return_column": "Manager"}},
        {"op": "add_summary", "sheet": "Claims", "group_by": "Status", "measures": [{"agg": "count"}, {"agg": "sum", "column": "Amount"}]},
        {"op": "conditional_format", "sheet": "Claims", "column": "Amount", "rule": "greater_than", "value": 1000, "color": "amber"},
    ])
    ws = wb["Claims"]
    assert ws["D2"].value == '=IFERROR(INDEX(Teams!$B$2:$B$4,MATCH(C2,Teams!$A$2:$A$4,0)),"")'
    sm = wb["Summary"]
    assert [sm.cell(r, 1).value for r in (4, 5, 6)] == ["Open", "Pending", "Closed"]   # dropdown order
    assert sm["C4"].value == "=SUMIFS(Claims!$F$2:$F$7,Claims!$G$2:$G$7,tblSummaryStatus[[#This Row],[Status]])"
    assert sm["C4"].value == sm["C5"].value              # same formula on every row (a proper table column)
    assert "tblSummaryStatus" in sm.tables


def test_rename_sheet_updates_references(claims):
    res, wb = apply(claims, [{"op": "rename_sheet", "sheet": "Claims", "new_name": "Claims 2026"}])
    assert wb["Report"]["B1"].value == "='Claims 2026'!E9"
    assert "'Claims 2026'" in wb["Report"]._charts[0].series[0].val.numRef.f


def test_failed_batch_leaves_workbook_as_it_was(claims):
    xw = ExpertWorkbook.open(claims)
    with pytest.raises(OpError):
        xw.apply([{"op": "insert_column", "sheet": "Claims", "header": "X"},
                  {"op": "sort", "sheet": "Claims", "by": "Nope"}])
    assert [c.value for c in xw.wb["Claims"][1]][:7] == ["Ref", "Member", "Team", "Received", "Amount", "Status", "VAT"]


def test_helpful_errors(claims):
    with pytest.raises(OpError, match="Did you mean 'Amount'"):
        apply(claims, [{"op": "sort", "sheet": "Claims", "by": "Amont"}])
    with pytest.raises(OpError, match="no sheet called"):
        apply(claims, [{"op": "sort", "sheet": "Claimz", "by": "Amount"}])


def test_convert_to_table_and_inspect(claims):
    xw = ExpertWorkbook.open(claims)
    xw.apply([{"op": "convert_to_table", "sheet": "Teams"}], requested_by="pytest")
    info = xw.inspect()
    teams = next(s for s in info["sheets"] if s["name"] == "Teams")["tables"][0]
    assert teams["is_excel_table"] and teams["rows"] == 3
    claims_cols = next(s for s in info["sheets"] if s["name"] == "Claims")["tables"][0]["columns"]
    assert next(c for c in claims_cols if c["header"] == "Status")["dropdown"] == ["Open", "Pending", "Closed"]


# --------------------------------------------------------------------------- AI-safe workbooks stay in sync


def test_expert_edits_keep_adlc_workbooks_valid(built):
    from adlc_workbook import AdlcWorkbook, validate_workbook

    path = built("action-tracker")
    res, wb = apply(path, [
        {"op": "insert_column", "table": "tblActions", "header": "Priority", "after": "Status", "choices": ["High", "Low"]},
        {"op": "add_rows", "table": "tblActions", "rows": [{"Action": "Book room", "Owner": "Aoife", "Priority": "High"}]},
        {"op": "add_summary", "table": "tblActions", "group_by": "Owner"},
    ])
    assert res.version == "1.1"
    report = validate_workbook(wb)
    assert report.ok, report.text()
    awb = AdlcWorkbook.open(path)
    priority = next(c for c in awb.spec["sheets"][0]["tables"][0]["columns"] if c["header"] == "Priority")
    assert priority["type"] == "choice" and priority["choices"] == ["High", "Low"]
    assert wb["Change Log"]["A3"].value == "1.1"
    assert any(row[0].value == "Priority" for row in wb["README"].iter_rows())
    # ...and the original ADLC engine can carry on afterwards.
    awb.apply([{"op": "update_rows", "table": "actions", "id": "ACT-002", "set": {"Priority": "Low"}}], requested_by="pytest")
    awb.save()
    assert validate_workbook(load_workbook(path)).ok

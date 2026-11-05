"""A realistic, messy, hand-made workbook used to test the expert engine (synthetic data only)."""

from datetime import datetime

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation


def make_claims_workbook(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Claims"
    ws.append(["Ref", "Member", "Team", "Received", "Amount", "Status", "VAT"])
    for c in ws[1]:
        c.font = Font(bold=True)
    rows = [
        ("CLM-001", "PERSON_001", "Hospital", datetime(2026, 9, 2), 1200, "Open"),
        ("CLM-002", "PERSON_002", "Outpatient", datetime(2026, 9, 3), 85.5, "Closed"),
        ("CLM-003", "PERSON_003", "Hospital", datetime(2026, 9, 5), 640, "Open"),
        ("CLM-004", "PERSON_001", "Dental", datetime(2026, 9, 9), 220, "Pending"),
        ("CLM-005", "PERSON_004", "Hospital", datetime(2026, 9, 12), 3100, "Closed"),
        ("CLM-002", "PERSON_002", "Outpatient", datetime(2026, 9, 3), 85.5, "Closed"),  # duplicate
    ]
    for i, row in enumerate(rows, start=2):
        ws.append(list(row) + [f"=E{i}*0.23"])
        ws.cell(i, 4).number_format = "dd/mm/yyyy"
    ws["A9"], ws["E9"] = "Total", "=SUM(E2:E7)"
    ws["A9"].font = ws["E9"].font = Font(bold=True)
    dv = DataValidation(type="list", formula1='"Open,Pending,Closed"', allow_blank=True)
    dv.add("F2:F7")
    ws.add_data_validation(dv)
    ws.conditional_formatting.add("F2:F7", FormulaRule(formula=['$F2="Open"'], fill=PatternFill("solid", start_color="FFC7CE", end_color="FFC7CE")))
    ws.merge_cells("I1:J1")
    ws["I1"] = "Notes"
    ws.column_dimensions["B"].width = 18
    ws.freeze_panes = "A2"

    teams = wb.create_sheet("Teams")
    teams.append(["Team", "Manager", "Budget"])
    for t in [("Hospital", "Aoife", 50000), ("Outpatient", "Liam", 20000), ("Dental", "Niamh", 8000)]:
        teams.append(list(t))

    rep = wb.create_sheet("Report")
    rep["A1"], rep["B1"] = "Total claimed", "=Claims!E9"
    rep["A2"], rep["B2"] = "Open amount", '=SUMIFS(Claims!E2:E7,Claims!F2:F7,"Open")'
    rep["A3"], rep["B3"] = "Largest", "=MAX(Claims!$E$2:$E$7)"
    chart = BarChart()
    chart.add_data(Reference(ws, min_col=5, min_row=1, max_row=7), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=7))
    rep.add_chart(chart, "D2")
    wb.defined_names["ClaimAmounts"] = __import__("openpyxl").workbook.defined_name.DefinedName(
        "ClaimAmounts", attr_text="Claims!$E$2:$E$7")
    wb.save(path)
    return path

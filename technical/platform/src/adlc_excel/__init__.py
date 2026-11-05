"""Expert Excel engine: change ANY workbook the way an Excel expert would.

Inserting or deleting rows and columns fixes every formula, table, dropdown, highlight,
merged cell, named range and chart that points at moved cells. Adding rows extends
totals and lookups that covered the whole list. Deleted rows are kept on a separate sheet.
AI-safe (ADLC) workbooks keep their spec, version and Change Log in step.

    from adlc_excel import ExpertWorkbook
    xw = ExpertWorkbook.open("Book.xlsx")
    print(xw.describe())
    res = xw.apply([{"op": "add_rows", "sheet": "Claims", "rows": [{"Member": "PERSON_004", "Amount": 120}]}],
                   requested_by="Aoife")
    xw.save("Book (updated).xlsx"); print(res.text())
"""

from .ops import OPS, OpError
from .regions import TargetError, find_region
from .workbook import ExpertResult, ExpertWorkbook, changed_ranges

__all__ = ["OPS", "ExpertResult", "ExpertWorkbook", "OpError", "TargetError", "changed_ranges", "find_region"]

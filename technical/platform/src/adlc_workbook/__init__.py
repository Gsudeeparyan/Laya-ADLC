"""ADLC self-describing workbooks.

Every workbook built here carries its own structure (a spec), version and change log,
so any AI agent - in any new chat - can change one part without breaking the rest.

    from adlc_workbook import AdlcWorkbook, load_spec
    awb = AdlcWorkbook.build(load_spec("templates/workbooks/action-tracker.spec.yaml"))
    awb.save("Action Tracker.xlsx")

    awb = AdlcWorkbook.open("Action Tracker.xlsx")
    awb.apply([{"op": "add_column", "table": "actions",
                "column": {"header": "Priority", "type": "choice", "choices": ["High", "Medium", "Low"]}}],
              requested_by="Mary")
    awb.save()
"""

from .adopt import AdoptResult, adopt
from .diff import diff_files, diff_snapshots, snapshot
from .meta import MetaError, read_meta
from .ops import OPS, OpError
from .render import DriftError
from .spec import SpecError, load_spec, prepare_spec
from .validate import ValidationReport, validate_workbook
from .workbook import AdlcWorkbook, ChangeResult

__version__ = "1.0.0"

__all__ = [
    "AdlcWorkbook", "AdoptResult", "ChangeResult", "DriftError", "MetaError", "OPS", "OpError",
    "SpecError", "ValidationReport", "adopt", "diff_files", "diff_snapshots", "load_spec",
    "prepare_spec", "read_meta", "snapshot", "validate_workbook",
]

"""The hidden ``_ADLC`` sheet: the workbook's memory.

Layout (column A = key, column B = value):

    ADLC_WORKBOOK   | <warning text for humans>
    format_version  | 1
    workbook_id     | uuid
    template        | template id or blank
    title           | workbook title
    owner           | owner name
    version         | "1.3"
    created         | ISO-8601 timestamp
    updated         | ISO-8601 timestamp
    updated_by      | who asked for the last change
    spec_sha256     | sha256 of the canonical spec JSON (integrity check)
    spec_parts      | number of spec chunks
    spec_1 .. n     | spec JSON split into chunks of at most 30,000 characters

Any agent (or the engine) reads this sheet first, so the structure survives across chats.
"""

from __future__ import annotations

import hashlib
import json

from openpyxl.styles import Font

META_SHEET = "_ADLC"
MARKER = "ADLC_WORKBOOK"
FORMAT_VERSION = 1
CHUNK = 30_000
WARNING = (
    "This hidden sheet lets AI agents and the ADLC engine change this workbook safely. "
    "Please do not edit, rename or delete it."
)
META_KEYS = (
    "format_version", "workbook_id", "template", "title", "owner", "version",
    "created", "updated", "updated_by",
)


def canonical_json(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def spec_hash(spec: dict) -> str:
    return hashlib.sha256(canonical_json(spec).encode("utf-8")).hexdigest()


def is_adlc(wb) -> bool:
    return META_SHEET in wb.sheetnames and wb[META_SHEET]["A1"].value == MARKER


def write_meta(wb, meta: dict, spec: dict) -> None:
    if META_SHEET in wb.sheetnames:
        del wb[META_SHEET]
    ws = wb.create_sheet(META_SHEET)
    ws.sheet_state = "hidden"
    ws["A1"], ws["B1"] = MARKER, WARNING
    ws["A1"].font = Font(bold=True)
    text = canonical_json(spec)
    parts = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)] or [""]
    rows = [(k, meta.get(k, "")) for k in META_KEYS]
    rows += [("spec_sha256", spec_hash(spec)), ("spec_parts", len(parts))]
    rows += [(f"spec_{i}", p) for i, p in enumerate(parts, start=1)]
    for r, (k, v) in enumerate(rows, start=2):
        ws.cell(row=r, column=1, value=k)
        cell = ws.cell(row=r, column=2, value="" if v is None else str(v))
        cell.data_type = "s"  # never let a value that starts with '=' become a formula
        cell.number_format = "@"
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 100


class MetaError(ValueError):
    pass


def read_meta(wb) -> tuple[dict, dict]:
    """Return (meta, spec). Raises MetaError if the sheet is missing or damaged."""
    if not is_adlc(wb):
        raise MetaError("This workbook has no ADLC sheet, so it was not built by ADLC (try 'adopt').")
    ws = wb[META_SHEET]
    values = {}
    for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        if row[0]:
            values[str(row[0])] = "" if row[1] is None else str(row[1])
    try:
        parts = int(values.get("spec_parts", "0"))
        text = "".join(values[f"spec_{i}"] for i in range(1, parts + 1))
        spec = json.loads(text)
    except (KeyError, ValueError) as exc:
        raise MetaError(f"The ADLC sheet is damaged and the spec cannot be read ({exc}).") from exc
    meta = {k: values.get(k, "") for k in META_KEYS}
    hash_ok = values.get("spec_sha256") == spec_hash(spec)
    from .spec import normalise_loaded

    spec = normalise_loaded(spec)
    # A mismatch usually means a hand edit (or an agent that hashed slightly differently).
    # It is reported by validate() rather than locking people out of their workbook.
    meta["integrity"] = "ok" if hash_ok else "mismatch"
    return meta, spec


def bump_version(version: str) -> str:
    try:
        major, minor = str(version or "1.0").split(".")[:2]
        return f"{int(major)}.{int(minor) + 1}"
    except ValueError:
        return "1.1"

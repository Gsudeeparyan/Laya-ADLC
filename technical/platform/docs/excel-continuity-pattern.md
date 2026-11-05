# The Excel continuity pattern: self-describing ("AI-safe") workbooks

**Status:** normative, format version 1. The Copilot agents (`excel-workbook-builder`, `excel-expert`, `project-planner`) and the Python engine (`src/adlc_workbook`) both follow this document. If you change it, change both, and add a test.

## The problem

Staff ask an AI to create a workbook, and it does. A week later they ask for one small change, in a new chat. The AI no longer knows how the workbook was built, so it guesses: it rebuilds the file, renames columns, drops formulas, loses dropdowns, or edits the wrong range. On the free Copilot Chat tier, agents also have **no memory between chats** and **cannot read SharePoint** (that needs pay-as-you-go billing). So the knowledge can't live in the agent.

## The solution: the file carries its own memory

Every ADLC workbook stores its own **structure (the spec)**, **version** and **change history** inside the file. Any agent in any chat, or the engine, reads that first and changes only what was asked. Nothing depends on chat history.

```mermaid
flowchart LR
    U[Person uploads workbook] --> R[Agent reads hidden _ADLC sheet]
    R --> P["Agent proposes changes in plain words<br/>(change operations)"]
    P -->|person replies OK| A[Apply ONLY those changes]
    A --> V[Re-check: structure matches spec,<br/>nothing else changed]
    V --> L[Bump version, add Change Log row,<br/>rewrite spec in _ADLC]
    L --> D[Person downloads and saves over<br/>the old file in SharePoint]
```

## Workbook layout

| Sheet | Visible | Purpose |
|---|---|---|
| `README` | yes, first | Title, purpose, owner, version, how to use it, sheet list, a table describing every column, and "how to change this with AI". Regenerated on every change. |
| data sheets | yes | One growing **Excel Table** per sheet (dashboards may hold small summary tables and charts). |
| `Settings` | yes, if any | Numbers that formulas use (e.g. "due soon" days). Each value cell has a defined name `p_<key>`. People can edit the yellow cells. |
| `Change Log` | yes | Table `tblChangeLog`: Version, Date, Requested by, Tool, Summary, Changes, Technical details. |
| `_Lists` | hidden | Only when a dropdown list is too long to store inline. Ranges named `lst_<table>_<column>`. |
| `_ADLC` | hidden | The workbook's memory (below). |

## Data rules

- All data lives in **Excel Tables** (ListObjects), normally named `tbl<Name>`.
- Every growing table has exactly one **ID column** (`type: id`). IDs are `id_prefix` + a 3-digit number (`ACT-007`). IDs are never reused or renumbered. Rows are updated and deleted **by ID, never by position**.
- Each column has a stable `key` (lower_snake_case) and a display `header`. Headers may be renamed; keys never change.
- Headers must not contain `[ ] # '` or line breaks, because they break structured references.
- **Calculated columns** use structured references and are written in the file form `tblActions[[#This Row],[Due date]]`. The Excel-UI shorthand `[@[Due date]]` is **not valid inside the file**. Writing it makes Excel refuse to open the workbook. Newer functions need the `_xlfn.` prefix in the file (`_xlfn.IFS`). Dynamic-array functions (FILTER, UNIQUE, SORT, SORTBY, SEQUENCE, LET, LAMBDA) are not allowed in table columns.
- Calculated cells are shaded light grey; input cells are not.
- Text that starts with `=` (for example, a formula shown as help text in the README) must be stored as text, never as a formula.
- A table may only grow into empty cells. If something sits directly below or to the right (e.g. a totals row), the change is refused with a plain-English explanation. Nothing is ever overwritten.

## The `_ADLC` sheet

Column A holds keys and column B holds values, all stored as text.

| Row | Key | Value |
|---|---|---|
| 1 | `ADLC_WORKBOOK` | warning text for humans |
| 2 | `format_version` | `1` |
| 3 | `workbook_id` | UUID |
| 4 | `template` | template id, `adopted`, or blank |
| 5 | `title` | workbook title |
| 6 | `owner` | owner |
| 7 | `version` | `MAJOR.MINOR`, starting at `1.0`; each change adds 0.1 |
| 8 | `created` | ISO-8601 date-time |
| 9 | `updated` | ISO-8601 date-time |
| 10 | `updated_by` | who asked for the last change |
| 11 | `spec_sha256` | sha256 of `json.dumps(spec, sort_keys=True, separators=(",",":"), ensure_ascii=False)` |
| 12 | `spec_parts` | number of chunks N |
| 13.. | `spec_1` .. `spec_N` | the spec JSON, split into chunks of at most 30,000 characters (an Excel cell holds 32,767) |

The checksum detects hand edits. A mismatch is reported as a **warning** by `validate` and never locks anyone out. The next engine change rewrites it.

## The spec

The spec describes **structure only, never data**. Seed rows in a template spec are used once at build time and are not stored.

```yaml
adlc_spec: 1
workbook:
  title: Action Tracker
  template: action-tracker
  purpose: Keep track of actions...
  owner: ""
  how_to_use: ["Add one row per action...", "..."]
parameters:                      # -> Settings sheet, named p_<key>
  - {key: due_soon_days, label: "Days before...", type: integer, value: 7, description: "..."}
sheets:
  - name: Actions
    description: One row per action.
    tables:
      - key: actions             # stable id used by change operations
        name: tblActions         # Excel table name
        anchor: A1
        id_prefix: ACT-
        columns:
          - {key: id, header: ID, type: id}
          - {key: status, header: Status, type: choice, required: true,
             choices: [Not started, In progress, Blocked, Done],
             highlights: [{when: equals, value: Done, color: green}]}
          - {key: days_left, header: Days left, type: formula,
             formula: '=IF([@[Due date]]="","",[@[Due date]]-TODAY())'}   # normalised on load
  - name: Dashboard
    tables:
      - key: status_summary
        name: tblStatusSummary
        rows_from: {table: actions, column: status}   # one row per dropdown option, kept in sync
        columns:
          - {key: status, header: Status, type: text}
          - {key: count, header: Actions, type: formula, formula: '=COUNTIF(tblActions[Status],[@Status])'}
    charts:
      - {key: status_chart, type: column, title: Actions by status, table: status_summary,
         category: status, values: [count], anchor: E2}
```

**Column types:**

| Type | What it holds |
|---|---|
| `id` | automatic ID |
| `text` | short text |
| `long_text` | wrapped text |
| `number`, `integer` | numbers (`min`/`max` optional) |
| `currency` | € amount |
| `percent` | percentage (0.5 means 50%) |
| `date` | date, shown as dd/mm/yyyy |
| `choice` | dropdown |
| `yes_no` | Yes/No dropdown |
| `formula` | calculated column |

Adopted workbooks may also use `formula_a1` + `formula_row` for older A1-style formulas, which are translated row by row.

**Highlights:**
- `when` is one of: equals, not_equals, less_than, greater_than, less_or_equal, greater_or_equal, blank, not_blank, contains.
- `value` gives a fixed value; use `value_formula` to compare against something like `p_due_soon_days`.
- `color` is one of: green, amber, red, grey, blue.
- Add `whole_row: true` to colour the whole row.

`required: true` columns turn light red when blank on a row that has other data.

**Charts** are declared in the spec and re-drawn on every save. That keeps them pointing at the right rows and avoids duplicates.

## Change operations

Every change is expressed as a list of operations. Agents show them to the person in plain words first. The engine applies them **atomically**: if one fails, nothing is written.

| Op | Required fields | Notes |
|---|---|---|
| `add_column` | `table`, `column` | optional `after` (column key/header, or `start`) and `fill_existing` (value for existing rows) |
| `rename_column` | `table`, `column`, `header` | updates every formula that refers to the column |
| `remove_column` | `table`, `column` | refused if a formula, chart or summary uses it; ID can't be removed |
| `set_formula` | `table`, `column`, `formula` | refused over typed values unless `force: true` |
| `set_choices` | `table`, `column`, `choices` | `mode`: replace (default), add or remove; refused if rows still use a removed value unless `force: true` |
| `set_format` (alias `update_column`) | `table`, `column` | any of: number_format, width, description, required, min, max, highlights |
| `add_rows` | `table`, `rows` | values keyed by column key or header; IDs filled automatically; values checked against types and dropdowns |
| `update_rows` | `table`, `id` or `ids`, `set` | IDs can't be changed |
| `delete_rows` | `table`, `ids` | |
| `add_table` | `sheet`, `table` | creates the sheet if needed; optional seed `rows` |
| `set_parameter` | `key`, `value` | creates a new setting if `label` is given |
| `add_chart` / `remove_chart` | `sheet`, `chart` | |
| `set_workbook_info` | any of: title, purpose, owner, how_to_use | |

`table` accepts the table key, table name or sheet name. `column` accepts the key or header.

Example (`ops.yaml`):

```yaml
ops:
  - op: add_column
    table: actions
    after: status
    column: {header: Priority, type: choice, choices: [High, Medium, Low]}
    fill_existing: Medium
  - op: update_rows
    table: actions
    id: ACT-001
    set: {Status: Done}
```

## Adopting an existing workbook

`adopt` makes an ordinary spreadsheet AI-safe with as little change as possible:
- **What it detects:**
  - each sheet's header row and data block (or an existing Excel Table);
  - column types, including dropdown options from existing data validation;
  - formula columns.
- **What it changes:**
  - the block becomes an Excel Table, and the original formatting is kept;
  - an `ID` column is added at the right-hand end if there is none;
  - README, Change Log and `_ADLC` sheets are added.
- **Where it stops:**
  - a totals row at the bottom is left outside the table, and the person is told to move it before adding rows;
  - merged cells inside the data stop adoption of that sheet.
- **What it warns about:** pivot tables, charts, shapes, macros and external links.

## Worked example for agents

[`everyone/skills/excel-expert/references/apply_change_example.py`](../../../non-technical/everyone/skills/excel-expert/references/apply_change_example.py) shows the Editor protocol in plain openpyxl, with no engine: read `_ADLC`, add a row, add a dropdown column, then write the version, spec, checksum, Change Log and README. `technical/platform/tests/test_protocol_compat.py` runs it in an isolated Python and checks the engine accepts the result. That test guarantees that what the skills tell Copilot to do stays compatible with the format.

## Using the engine

```text
python -m adlc_workbook build    spec.yaml out.xlsx [--owner NAME]
python -m adlc_workbook apply    book.xlsx ops.yaml --by NAME [-o out.xlsx] [--summary TEXT]
python -m adlc_workbook validate book.xlsx      # drift check; exit code 1 on errors
python -m adlc_workbook inspect  book.xlsx      # version, tables, columns, settings
python -m adlc_workbook spec     book.xlsx      # stored spec as YAML
python -m adlc_workbook adopt    book.xlsx [-o out.xlsx] [--dry-run]
python -m adlc_workbook diff     before.xlsx after.xlsx
```

`validate` reports:
- **errors:** missing tables or columns; headers changed by hand; typed values where a formula belongs; duplicate IDs; missing settings;
- **warnings:** blank required cells; values not in a dropdown; rows without IDs; checksum mismatch.

## Known limits

- openpyxl does not calculate formulas. A file saved by the engine or an agent shows formula results once it is opened in Excel; `fullCalcOnLoad` is set so this happens automatically. Agents reading such a file should work the logic out in pandas.
- Pivot tables survive but need a refresh in Excel. Charts that are not in the spec are kept, but some formatting may be simplified. Shapes and macros (`.xlsm`) are not kept.
- One growing table per sheet.

## Where this goes next

The engine is pure Python with openpyxl and PyYAML and needs no network. That means it can later move, unchanged, into:
- the `scripts/` folder of a Microsoft 365 custom skill (sandboxed, no network), once Laya's licensing allows;
- an Azure Function used as a Copilot Studio tool, writing directly to SharePoint through Microsoft Graph, once pay-as-you-go is enabled.

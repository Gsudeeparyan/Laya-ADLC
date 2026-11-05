"""Charts are declared in the spec and re-created on every save.

That keeps them pointing at the right rows after tables grow or shrink, and avoids the
formatting loss that comes from round-tripping existing charts through openpyxl.
"""

from __future__ import annotations

from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.utils.cell import range_boundaries

from .spec import find_column, find_table


def _new_chart(kind: str):
    if kind in ("column", "bar"):
        chart = BarChart()
        chart.type = "col" if kind == "column" else "bar"
        chart.legend = None
        return chart
    if kind == "line":
        return LineChart()
    return PieChart()


def render_charts(wb, spec) -> int:
    """Replace the charts on every sheet that declares charts. Returns how many were drawn."""
    drawn = 0
    for sheet in spec["sheets"]:
        if not sheet.get("charts") or sheet["name"] not in wb.sheetnames:
            continue
        ws = wb[sheet["name"]]
        ws._charts = []
        for c in sheet["charts"]:
            src_sheet, table = find_table(spec, c["table"])
            src_ws = wb[src_sheet["name"]]
            t = src_ws.tables[table["name"]]
            c0, r0, _, r1 = range_boundaries(t.ref)
            headers = [col["key"] for col in table["columns"]]
            cat_idx = c0 + headers.index(find_column(table, c["category"])["key"])
            chart = _new_chart(c["type"])
            chart.title = c.get("title") or None
            chart.width, chart.height = c.get("width", 16), c.get("height", 8)
            for v in c["values"]:
                v_idx = c0 + headers.index(find_column(table, v)["key"])
                data = Reference(src_ws, min_col=v_idx, min_row=r0, max_row=r1)
                chart.add_data(data, titles_from_data=True)
            chart.set_categories(Reference(src_ws, min_col=cat_idx, min_row=r0 + 1, max_row=r1))
            if len(c["values"]) > 1 and c["type"] != "pie":
                from openpyxl.chart.legend import Legend

                chart.legend = Legend()
            ws.add_chart(chart, c.get("anchor", "H2"))
            drawn += 1
    return drawn

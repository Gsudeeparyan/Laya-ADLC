"""Build the ready-made templates for the ADLC Templates folder in SharePoint.

    python tools/build_templates.py            # build all
    python tools/build_templates.py raid-log   # build one

- non-technical/templates/workbooks/*.spec.yaml -> ready-to-use/templates/<Title>.xlsx  (AI-safe, built by the engine, then validated)
- non-technical/templates/documents/*.md        -> ready-to-use/templates/<Title>.docx  (Word, ending with an ADLC Record)

To prove the workbooks open cleanly in real Excel on Windows, run tools/excel_check.ps1 on
ready-to-use/templates afterwards.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import READY_TEMPLATES as OUT, ROOT, SRC, TEMPLATE_DOCUMENTS as DOCS, TEMPLATE_WORKBOOKS as SPECS, TOOLS  # noqa: E402

sys.path.insert(0, str(SRC))

from adlc_workbook import AdlcWorkbook, load_spec  # noqa: E402



def build(names: list[str] | None = None) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    built = []
    for spec_path in sorted(SPECS.glob("*.spec.yaml")):
        slug = spec_path.name.removesuffix(".spec.yaml")
        if names and slug not in names:
            continue
        spec = load_spec(spec_path)
        awb = AdlcWorkbook.build(spec, requested_by="ADLC template build", tool="build_templates.py")
        target = OUT / f"{spec['workbook']['title']}.xlsx"
        awb.save(target)
        report = awb.validate()
        status = "OK" if report.ok else "PROBLEMS"
        print(f"{status:8} {target.relative_to(ROOT)}")
        if not report.ok:
            print(report.text())
            raise SystemExit(1)
        built.append(target)
    return built


def build_documents(names: list[str] | None = None) -> list[Path]:
    try:
        from docx import Document
    except ImportError:
        print("python-docx is not installed; skipped the Word templates (pip install python-docx).")
        return []
    sys.path.insert(0, str(TOOLS))
    from build_staff_guide import render_markdown

    built = []
    for md in sorted(DOCS.glob("*.md")):
        if names and md.stem not in names:
            continue
        text = md.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").split(":")[0].strip()
        doc = Document()
        render_markdown(doc, text)
        target = OUT / f"{title} template.docx"
        doc.save(target)
        print(f"OK       {target.relative_to(ROOT)}")
        built.append(target)
    return built


if __name__ == "__main__":
    build(sys.argv[1:] or None)
    build_documents(sys.argv[1:] or None)

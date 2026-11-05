from pathlib import Path

import pytest

from adlc_workbook import AdlcWorkbook, load_spec

from paths import TEMPLATE_WORKBOOKS as SPECS


@pytest.fixture
def spec_path():
    return lambda name: SPECS / f"{name}.spec.yaml"


@pytest.fixture
def built(tmp_path):
    """Build a template into tmp_path and return the saved file path."""

    def _build(name: str) -> Path:
        awb = AdlcWorkbook.build(load_spec(SPECS / f"{name}.spec.yaml"), requested_by="pytest")
        return awb.save(tmp_path / f"{name}.xlsx")

    return _build

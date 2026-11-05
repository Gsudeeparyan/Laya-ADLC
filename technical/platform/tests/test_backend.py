"""SharePoint backend tests with a fake Microsoft Graph (no network, synthetic data)."""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from paths import BACKEND  # noqa: E402

sys.path.insert(0, str(BACKEND))

from graph import ConflictError, DriveFile  # noqa: E402
from service import ServiceError, WorkbookService  # noqa: E402
from vault_store import InMemoryVaultStore  # noqa: E402

from test_pii import PPSN_A, PPSN_B  # noqa: E402


class FakeGraph:
    def __init__(self):
        self.files: dict[str, tuple[DriveFile, bytes]] = {}
        self.etag_counter = 0
        self.before_upload = None

    def add(self, name: str, content: bytes) -> str:
        url = f"https://laya.sharepoint.com/sites/team/Shared Documents/{name}"
        self.etag_counter += 1
        self.files[url] = (DriveFile("drive1", f"item{len(self.files) + 1}", name, f"etag{self.etag_counter}", "folder1", url), content)
        return url

    def _find(self, f):
        return next(u for u, (df, _) in self.files.items() if df.item_id == f.item_id)

    def resolve(self, url):
        if url not in self.files:
            from graph import GraphError
            raise GraphError(404, "I can't find that file.")
        return self.files[url][0]

    def download(self, f):
        return self.files[self._find(f)][1]

    def upload(self, f, content):
        if self.before_upload:
            self.before_upload()
        url = self._find(f)
        current, _ = self.files[url]
        if current.etag != f.etag:
            raise ConflictError(412, "The file was changed by someone else since I read it. Nothing was saved - please ask again.")
        self.etag_counter += 1
        new = DriveFile(current.drive_id, current.item_id, current.name, f"etag{self.etag_counter}", current.parent_id, url)
        self.files[url] = (new, content)
        return new

    def create_sibling(self, f, name, content):
        url = self.add(name, content)
        return self.files[url][0]


def members_bytes():
    wb = Workbook()
    ws = wb.active
    ws.title = "Members"
    ws.append(["Member Name", "PPS Number", "Date of birth", "Plan", "Premium", "Notes"])
    ws.append(["Mary Byrne", PPSN_A, datetime(1984, 3, 12), "Gold", 1450, "Mary Byrne asked about dental cover"])
    ws.append(["John Murphy", PPSN_B, datetime(1979, 7, 1), "Silver", 980, "Call on 087 765 4321"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def env():
    graph = FakeGraph()
    url = graph.add("Members.xlsx", members_bytes())
    svc = WorkbookService(graph, InMemoryVaultStore(), user_id="user-1", user_name="Aoife Tester")
    return graph, svc, url


def no_pii(obj):
    text = json.dumps(obj, default=str)
    return not any(s in text for s in ("Mary Byrne", "John Murphy", PPSN_A, PPSN_B, "087 765 4321"))


def test_inspect_returns_tokens_only(env):
    graph, svc, url = env
    info = svc.inspect(url)
    assert no_pii(info)
    cols = info["workbook"]["sheets"][0]["tables"][0]["columns"]
    member = next(c for c in cols if c["header"] == "Member Name")
    assert member["personal_data"] == "PERSON" and member["sample"][0] == "PERSON_001"
    assert "personal data" in info["privacy"]


def test_query_filters_on_tokens_and_returns_tokens(env):
    graph, svc, url = env
    svc.inspect(url)
    res = svc.query(url, sheet="Members", where={"Member Name": "PERSON_002"})
    assert res["total_matching_rows"] == 1 and res["rows"][0][3] == "Silver"
    assert no_pii(res)
    res = svc.query(url, where=[{"column": "Premium", "op": "greater_than", "value": 1000}], columns=["Member Name", "Plan"])
    assert res["rows"] == [["PERSON_001", "Gold"]]


def test_apply_writes_real_values_but_reports_tokens(env):
    graph, svc, url = env
    svc.inspect(url)
    res = svc.apply(url, [
        {"op": "update_rows", "sheet": "Members", "where": {"Member Name": "PERSON_001"}, "set": {"Plan": "Platinum"}},
        {"op": "add_rows", "sheet": "Members", "rows": [{"Member Name": "PERSON_002", "Plan": "Bronze", "Premium": 500}]},
    ], summary="Upgrade PERSON_001")
    assert res["saved"] and no_pii(res)
    ws = load_workbook(io.BytesIO(graph.files[url][1]))["Members"]
    assert ws["D2"].value == "Platinum"
    assert ws["A4"].value == "John Murphy" and ws["D4"].value == "Bronze"


def test_preview_never_saves(env):
    graph, svc, url = env
    before = graph.files[url][1]
    res = svc.preview(url, [{"op": "insert_column", "sheet": "Members", "header": "Priority"}])
    assert not res["saved"] and graph.files[url][1] == before
    assert "Added column 'Priority'" in res["changes"][0]


def test_someone_elses_change_is_never_overwritten(env):
    graph, svc, url = env

    def someone_edits():
        df, content = graph.files[url]
        graph.files[url] = (DriveFile(df.drive_id, df.item_id, df.name, "etag-by-colleague", df.parent_id, df.web_url), content)

    graph.before_upload = someone_edits
    with pytest.raises(ConflictError):
        svc.apply(url, [{"op": "insert_column", "sheet": "Members", "header": "Priority"}])


def test_pii_scan_clean_copy_and_restore(env):
    graph, svc, url = env
    scan = svc.pii_scan(url)
    assert scan["risk"] == "personal" and scan["found"]["PPSN"] == 2 and no_pii(scan)
    assert all("example" not in w for w in scan["where"])
    made = svc.pii_clean_copy(url)
    clean_url = next(u for u, (df, _) in graph.files.items() if df.name == "Members (PII removed).xlsx")
    assert made["restorable"] and no_pii(made)
    clean_ws = load_workbook(io.BytesIO(graph.files[clean_url][1]))["Members"]
    assert clean_ws["A2"].value == "PERSON_001" and clean_ws["B3"].value == "PPSN_002"
    # Someone works on the clean copy with any AI tool, then restores it.
    restored = svc.pii_restore_copy(clean_url)
    back_url = next(u for u, (df, _) in graph.files.items() if df.name == restored["restored_copy"])
    back = load_workbook(io.BytesIO(graph.files[back_url][1]))["Members"]
    assert back["A2"].value == "Mary Byrne" and back["B3"].value == PPSN_B
    with pytest.raises(ServiceError, match="key"):
        svc.pii_restore_copy(url)


def test_wrong_file_type(env):
    graph, svc, url = env
    doc_url = graph.add("Notes.docx", b"not really a docx")
    with pytest.raises(ServiceError, match=".xlsx"):
        svc.inspect(doc_url)

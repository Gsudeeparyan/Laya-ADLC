"""PII guard tests. All data here is synthetic - generated names and numbers with valid check digits."""

from datetime import datetime

import pytest
from docx import Document
from openpyxl import Workbook, load_workbook

from adlc_pii import Policy, Vault, classify_header, find_in_text, iban_valid, luhn_valid, ppsn_valid
from adlc_pii.scrub import restore_file, scan_file, scrub_file, scrub_text


def make_ppsn(seven: str, second: str = "") -> str:
    total = sum(int(d) * w for d, w in zip(seven, range(8, 1, -1)))
    if second and second != "W":
        total += (ord(second) - 64) * 9
    return seven + ("W" if total % 23 == 0 else chr(64 + total % 23)) + second


def make_iban(bank: str = "AIBK", sort: str = "931152", account: str = "12345678") -> str:
    bban = bank + sort + account
    number = int("".join(str(int(ch, 36)) for ch in bban + "IE00"))
    return f"IE{98 - number % 97:02d}{bban}"


PPSN_A, PPSN_B = make_ppsn("1234567"), make_ppsn("7654321", "A")
IBAN_A = make_iban()


def test_validators():
    assert ppsn_valid(PPSN_A) and ppsn_valid(PPSN_B) and ppsn_valid(PPSN_A.lower())
    assert not ppsn_valid("1234567" + ("A" if PPSN_A[-1] != "A" else "B"))
    assert iban_valid(IBAN_A) and iban_valid(" ".join(IBAN_A[i:i + 4] for i in range(0, 22, 4)))
    assert not iban_valid(IBAN_A[:-1] + ("0" if IBAN_A[-1] != "0" else "1"))
    assert luhn_valid("4111 1111 1111 1111") and not luhn_valid("4111 1111 1111 1112")


@pytest.mark.parametrize("text, ptype", [
    (f"PPS {PPSN_A} on file", "PPSN"),
    (f"pay to {IBAN_A} please", "IBAN"),
    ("card 4111-1111-1111-1111", "CARD"),
    ("email aoife.byrne@example.ie today", "EMAIL"),
    ("ring 087 123 4567 after 5", "PHONE"),
    ("ring +353 87 123 4567", "PHONE"),
    ("Eircode D02 X285", "EIRCODE"),
    ("DOB: 12/03/1984", "DATE_OF_BIRTH"),
    ("lives at 14 Main Street", "ADDRESS"),
    ("Spoke with Mary Byrne", "PERSON"),
    ("Dr. Ciarán Ó Súilleabháin called", "PERSON"),
    ("history of diabetes", "HEALTH"),
])
def test_finds_each_type(text, ptype):
    assert ptype in {f.type for f in find_in_text(text)}


@pytest.mark.parametrize("text", [
    "Will May attend the Monday meeting?",
    "Laya Healthcare Plan B renewal is due in March.",
    "Contact Dublin office about invoice 2026-0145.",
    "Order 1234567 shipped; total 4,500 items.",
    "The Team Lead approved the change on 06/10/2026.",
])
def test_no_false_positives(text):
    assert [f for f in find_in_text(text) if f.type != "HEALTH"] == []


@pytest.mark.parametrize("header, expected", [
    ("Member Name", "PERSON"), ("Surname", "PERSON"), ("Product name", None), ("Team name", None),
    ("PPS No.", "PPSN"), ("Owner", "STAFF_NAME"), ("Diagnosis", "HEALTH"), ("DOB", "DATE_OF_BIRTH"),
    ("Policy Number", "MEMBER_ID"), ("Mobile", "PHONE"), ("E-mail address", "EMAIL"), ("Eircode", "EIRCODE"),
    ("Status", None), ("Amount (€)", None),
])
def test_header_classification(header, expected):
    assert classify_header(header) == expected


def test_same_value_gets_same_token():
    clean, vault = scrub_text("Mary Byrne rang. Later mary byrne emailed.")
    assert clean.count("PERSON_001") == 2 and len(vault) == 1


# --------------------------------------------------------------------------- Excel


@pytest.fixture
def members_xlsx(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Members"
    ws.append(["Member Name", "PPS Number", "Date of birth", "Mobile", "Email", "Diagnosis", "Amount", "Notes", "Owner", "Double"])
    people = [
        ("Mary Byrne", PPSN_A, datetime(1984, 3, 12), 871234567, "mary.byrne@example.ie", "Diabetes", 120.5,
         "Mary Byrne asked about her claim", "Aoife"),
        ("John Murphy", PPSN_B, datetime(1979, 7, 1), 861112222, "j.murphy@example.ie", "Hip replacement", 900,
         "Call back on 087 765 4321", "Aoife"),
        ("Mary Byrne", PPSN_A, datetime(1984, 3, 12), 871234567, "mary.byrne@example.ie", "Diabetes", 60,
         "Second claim", "Liam"),
    ]
    for i, row in enumerate(people, start=2):
        ws.append(list(row) + [f"=G{i}*2"])
    path = tmp_path / "members.xlsx"
    wb.save(path)
    return path, people


def all_values(path):
    wb = load_workbook(path)
    return [c.value for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None]


def test_clean_workbook_removes_pii_and_keeps_the_rest(members_xlsx, tmp_path):
    path, people = members_xlsx
    out, report, vault = scrub_file(path, tmp_path / "clean.xlsx")
    values = all_values(out)
    text = " ".join(str(v) for v in values)
    for secret in ("Mary Byrne", "John Murphy", PPSN_A, PPSN_B, "mary.byrne@example.ie", "087 765 4321"):
        assert secret not in text
    assert 871234567 not in values and datetime(1984, 3, 12) not in values
    ws = load_workbook(out)["Members"]
    assert ws["A2"].value == ws["A4"].value == "PERSON_001"            # same person, same token
    assert ws["H2"].value == "PERSON_001 asked about her claim"         # name in free text matched to the column
    assert ws["F2"].value == "Diabetes"                                 # health kept (needed), but reported
    assert ws["G3"].value == 900 and ws["J2"].value == "=G2*2"          # numbers and formulas untouched
    assert ws["I2"].value == "Aoife"                                    # staff names kept by default
    assert report.risk == "special"
    assert report.counts["PPSN"] == 3 and report.counts["HEALTH"] >= 3


def test_restore_after_ai_edits(members_xlsx, tmp_path):
    path, people = members_xlsx
    out, report, vault = scrub_file(path, tmp_path / "clean.xlsx")
    vault_path = vault.save(tmp_path / "v.json")
    # Simulate the AI's work on the clean copy: sort rows, add a column and a summary line.
    wb = load_workbook(out)
    ws = wb["Members"]
    rows = sorted(list(ws.iter_rows(min_row=2, values_only=True)), key=lambda r: r[6])
    for r, row in enumerate(rows, start=2):
        for c, v in enumerate(row, start=1):
            ws.cell(r, c, v)
    ws["K1"], ws["K2"] = "Priority", "High"
    ws["A10"] = "Follow up with PERSON_002 and PERSON_001"
    edited = tmp_path / "clean - edited.xlsx"
    wb.save(edited)

    restored = restore_file(edited, Vault.load(vault_path), tmp_path / "final.xlsx")
    ws = load_workbook(restored)["Members"]
    names = [ws.cell(r, 1).value for r in range(2, 5)]
    assert sorted(names) == ["John Murphy", "Mary Byrne", "Mary Byrne"]
    by_name = {ws.cell(r, 1).value: r for r in range(2, 5)}
    r = by_name["John Murphy"]
    assert ws.cell(r, 2).value == PPSN_B and ws.cell(r, 4).value == 861112222
    assert ws.cell(r, 3).value == datetime(1979, 7, 1)
    assert ws["A10"].value == "Follow up with John Murphy and Mary Byrne"
    assert ws["K2"].value == "High"


def test_anonymise_profile_is_not_restorable(members_xlsx, tmp_path):
    path, _ = members_xlsx
    policy = Policy(profile="anonymise")
    out, report, vault = scrub_file(path, tmp_path / "anon.xlsx", policy)
    ws = load_workbook(out)["Members"]
    assert ws["A2"].value == "[PERSON]" and ws["C2"].value == "born 1984"
    assert not policy.restorable


def test_scan_changes_nothing(members_xlsx):
    path, _ = members_xlsx
    before = path.read_bytes()
    report = scan_file(path)
    assert report.risk == "special" and path.read_bytes() == before
    assert "PPS numbers" in report.text(cleaned=False)


def test_adlc_workbook_stays_valid_after_cleaning(built, tmp_path):
    from adlc_workbook import AdlcWorkbook, validate_workbook

    path = built("action-tracker")
    awb = AdlcWorkbook.open(path)
    awb.apply([{"op": "add_rows", "table": "actions", "rows": [
        {"Action": "Call Mary Byrne on 087 123 4567 about her claim", "Owner": "Aoife"}]}], requested_by="pytest")
    awb.save()
    out, report, vault = scrub_file(path, tmp_path / "clean.xlsx")
    wb = load_workbook(out)
    assert "PERSON_001" in wb["Actions"]["B3"].value and "PHONE_001" in wb["Actions"]["B3"].value
    assert validate_workbook(wb).ok


# --------------------------------------------------------------------------- Word and CSV


def test_docx_round_trip(tmp_path):
    doc = Document()
    doc.add_paragraph(f"Letter to Mary Byrne, 14 Main Street, Eircode D02 X285. PPS {PPSN_A}.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Name", "Policy number"
    table.cell(1, 0).text, table.cell(1, 1).text = "John Murphy", "POL-55512"
    path = tmp_path / "letter.docx"
    doc.save(path)
    out, report, vault = scrub_file(path, tmp_path / "clean.docx")
    clean = Document(str(out))
    text = "\n".join(p.text for p in clean.paragraphs) + " ".join(c.text for r in clean.tables[0].rows for c in r.cells)
    for secret in ("Mary Byrne", "John Murphy", PPSN_A, "D02 X285", "POL-55512", "14 Main Street"):
        assert secret not in text
    restored = Document(str(restore_file(out, vault, tmp_path / "back.docx")))
    assert restored.paragraphs[0].text == doc.paragraphs[0].text
    assert restored.tables[0].cell(1, 0).text == "John Murphy"


def test_csv_round_trip(tmp_path):
    path = tmp_path / "list.csv"
    path.write_text(f"Name,PPSN,Comment\nMary Byrne,{PPSN_A},Mary Byrne rang\n", encoding="utf-8")
    out, report, vault = scrub_file(path, tmp_path / "clean.csv")
    assert out.read_text(encoding="utf-8-sig").splitlines()[1] == "PERSON_001,PPSN_001,PERSON_001 rang"
    back = restore_file(out, vault, tmp_path / "back.csv")
    assert back.read_text(encoding="utf-8").splitlines()[1] == f"Mary Byrne,{PPSN_A},Mary Byrne rang"

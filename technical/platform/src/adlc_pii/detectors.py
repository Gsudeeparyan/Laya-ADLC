"""PII detectors tuned for Irish data.

Each detector finds candidate values in text. Where a format has a check digit (PPSN,
IBAN, payment cards) the candidate is validated, which keeps false positives low.
Column headings are the strongest signal for tables, so they are matched separately
(see HEADER_RULES and classify_header).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------- types

DIRECT = (
    "PERSON", "PPSN", "EMAIL", "PHONE", "ADDRESS", "EIRCODE", "IBAN", "CARD",
    "BANK_ACCOUNT", "MEMBER_ID", "IP_ADDRESS", "PASSPORT",
)
QUASI = ("DATE_OF_BIRTH",)
SPECIAL = ("HEALTH",)
LOW = ("STAFF_NAME",)
ALL_TYPES = DIRECT + QUASI + SPECIAL + LOW

LABELS = {
    "PERSON": "names of people",
    "STAFF_NAME": "staff names",
    "PPSN": "PPS numbers",
    "EMAIL": "email addresses",
    "PHONE": "phone numbers",
    "ADDRESS": "postal addresses",
    "EIRCODE": "Eircodes",
    "IBAN": "IBANs (bank accounts)",
    "CARD": "payment card numbers",
    "BANK_ACCOUNT": "bank account details",
    "MEMBER_ID": "member, policy or claim numbers",
    "IP_ADDRESS": "IP addresses",
    "PASSPORT": "passport numbers",
    "DATE_OF_BIRTH": "dates of birth",
    "HEALTH": "health information (special category)",
}


@dataclass
class Finding:
    type: str
    start: int
    end: int
    value: str
    method: str          # pattern | checksum | header | dictionary | known
    confidence: float


# --------------------------------------------------------------------------- validators


def ppsn_valid(text: str) -> bool:
    """PPSN: 7 digits + check letter + optional second letter. Weights 8..2, mod 23."""
    m = re.fullmatch(r"(\d{7})([A-WY])([A-IW]?)", text.upper().replace(" ", ""))
    if not m:
        return False
    digits, check, second = m.groups()
    total = sum(int(d) * w for d, w in zip(digits, range(8, 1, -1)))
    if second and second != "W":
        total += (ord(second) - 64) * 9
    expected = "W" if total % 23 == 0 else chr(64 + total % 23)
    return check == expected


def iban_valid(text: str) -> bool:
    s = re.sub(r"\s", "", text).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    if s.startswith("IE") and len(s) != 22:
        return False
    moved = s[4:] + s[:4]
    number = "".join(str(int(ch, 36)) for ch in moved)
    return int(number) % 97 == 1


def luhn_valid(text: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", text)]
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# --------------------------------------------------------------------------- dictionaries

FIRST_NAMES = set("""
Sean Seán John Patrick Pat Michael James David Daniel Conor Cian Jack Liam Noah Oisin Oisín Darragh
Adam Luke Fionn Tadhg Ryan Eoin Ciaran Ciarán Niall Shane Paul Brian Kevin Declan Colm Cathal Donal
Dónal Fergal Gerard Ger Thomas Tom Peter Stephen Eamon Eamonn Aidan Barry Brendan Cormac Dara Dermot
Diarmuid Enda Finbar Gavin Kieran Martin Neil Owen Padraig Pádraig Rory Ronan Ruairi Ruairí Seamus
Séamus Tim Timothy William Alan Anthony Christopher Denis Joseph Joe Matthew Robert Richard Andrew
Edward Francis Hugh Philip Vincent Mary Margaret Anne Ann Catherine Kate Bridget Brigid Siobhan
Siobhán Aoife Aine Áine Niamh Sinead Sinéad Orla Órla Ciara Clodagh Deirdre Emer Grainne Gráinne
Laoise Maire Máire Maeve Méabh Nuala Roisin Róisín Saoirse Sorcha Una Úna Caoimhe Eimear Fiona
Sarah Emma Emily Sophie Lucy Chloe Ella Amy Rachel Laura Lisa Claire Clare Elizabeth Helen Julie
Karen Louise Michelle Nicola Patricia Rebecca Susan Teresa Elaine Joan Kathleen Eileen Noreen
Maureen Geraldine Jennifer Jessica Hannah Leah Molly Ava Mia Isabelle Zoe Olivia Anna Ellen Eva
Nora Norah Ruth Sheila Tara Yvonne Carmel Colette Dympna Fidelma Gemma Aisling Ailbhe Aoibhinn
Cliona Clíona Eabha Muireann Ruth Sadhbh Shauna Ger Mairead Mairéad Breda Bernadette Noel Oliver
""".split())

SURNAMES = set("""
Murphy Kelly O'Sullivan Sullivan Walsh Smith O'Brien Brien Byrne Ryan O'Connor Connor O'Neill
O'Reilly Reilly Doyle McCarthy Gallagher O'Doherty Doherty Kennedy Lynch Murray Quinn Moore
McLoughlin O'Carroll Carroll Connolly Daly O'Connell Connell Wilson Dunne Brennan Burke Collins
Campbell Clarke Johnston Hughes O'Farrell Farrell Fitzgerald Brown Maguire Nolan Flynn Thompson
O'Callaghan Callaghan O'Donnell Duffy O'Mahony Mahony Boyle Healy O'Shea Shea Sweeney Hayes
Kavanagh Power McGrath Moran Brady Stewart Casey Foley Fitzpatrick O'Leary Leary McDonnell McMahon
MacMahon Donnelly Regan O'Regan Donovan O'Donovan Burns Flanagan Mullan Kane Robinson Cunningham
Griffin Kenny Sheehan Ward Whelan Lyons Reid Graham Higgins Cullen Keane Maher McKenna Scott Hogan
O'Keeffe Keeffe Magee McNamara MacDonald McDonald Hennessy Hegarty Tierney Molloy Carey Coleman
Cronin Dolan Egan Fagan Horgan Joyce Kearney Kirwan Lawlor Lennon Mooney Mulligan Nugent Phelan
Rooney Delaney Dempsey Devlin Dillon Gleeson Hanlon Hickey Kiely Kinsella Lawless Madden Mangan
Morrissey Mulcahy Murtagh O'Dwyer Dwyer O'Gorman Gorman O'Hara Hara O'Rourke Rourke Treacy Twomey
""".split())

NAME_PREFIXES = ("O'", "O’", "Mc", "Mac", "Ní ", "Nic ", "Ó ", "Mhic ", "Uí ")
# Capitalised words that follow a first name but are not surnames.
NOT_SURNAMES = set("""
Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July
August September October November December Laya Healthcare Health Ireland Irish Dublin Cork Galway
Limerick Waterford Street Road Avenue Team Group Hospital Clinic Insurance Policy Claims Claim Member
Members Services Service Centre Center Office Department Unit Ward The And Of For To In On At
""".split())

TITLES = r"(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Fr|Sr|Sir|Dame)"
_NAME_WORD = r"(?:O['’]|Mc|Mac|N[ií] |Nic |Ó |Mhic |U[ií] )?[A-ZÁÉÍÓÚ][a-záéíóú'’\-]+"

HEALTH_TERMS = sorted(set("""
diabetes diabetic cancer tumour tumor oncology chemotherapy radiotherapy leukaemia leukemia lymphoma
melanoma asthma copd epilepsy seizure stroke cardiac angina arrhythmia hypertension cholesterol
depression anxiety bipolar schizophrenia psychosis psychiatric anorexia bulimia adhd autism dementia
alzheimer's alzheimers parkinson's parkinsons arthritis osteoporosis hiv hepatitis pregnancy pregnant
maternity miscarriage ivf fertility surgery mri endoscopy colonoscopy biopsy physiotherapy
psychotherapy counselling rehabilitation addiction alcoholism overdose dialysis transplant disability
wheelchair diagnosis diagnosed prescription medication insulin antidepressant inpatient outpatient
palliative hospice obesity bariatric dermatology orthopaedic orthopedic cardiology neurology
gynaecology urology paediatric psychiatry oncologist cardiologist cataract hysterectomy mastectomy
""".split()) | {
    "heart attack", "heart failure", "blood pressure", "mental health", "eating disorder",
    "multiple sclerosis", "hip replacement", "knee replacement", "ct scan", "x-ray", "day case",
    "emergency department", "a&e", "intensive care", "gastric band", "kidney disease", "liver disease",
})

# --------------------------------------------------------------------------- column headings

HEADER_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("PPSN", ("pps", "ppsn", "personal public service")),
    ("IBAN", ("iban",)),
    ("CARD", ("card number", "credit card", "debit card", "card no", "pan")),
    ("BANK_ACCOUNT", ("account number", "account no", "acc no", "sort code", "bic", "bank account", "bank details")),
    ("EMAIL", ("email", "e-mail", "e mail", "mail address")),
    ("PHONE", ("phone", "mobile", "telephone", "tel", "contact number", "mob", "landline")),
    ("EIRCODE", ("eircode", "postcode", "post code", "zip")),
    ("DATE_OF_BIRTH", ("dob", "d o b", "date of birth", "birth date", "birthdate", "birthday")),
    ("PASSPORT", ("passport",)),
    ("IP_ADDRESS", ("ip address", "ip addr")),
    ("ADDRESS", ("address", "street", "addr", "address line", "residence", "home town")),
    ("MEMBER_ID", (
        "member number", "member no", "member id", "membership number", "membership no",
        "policy number", "policy no", "policy id", "policy ref", "claim number", "claim no",
        "claim id", "claim ref", "customer number", "customer id", "customer no", "scheme member",
    )),
    ("HEALTH", (
        "diagnosis", "condition", "illness", "procedure", "treatment", "medication", "medical",
        "clinical", "symptom", "disability", "icd", "admission reason", "reason for claim",
        "specialty", "speciality", "health",
    )),
    ("STAFF_NAME", (
        "owner", "assigned to", "assignee", "requested by", "raised by", "handler", "case handler",
        "agent", "manager", "team lead", "approver", "approved by", "reviewer", "author", "updated by",
    )),
    ("PERSON", (
        "name", "first name", "firstname", "forename", "surname", "last name", "lastname",
        "full name", "member name", "patient", "policyholder", "policy holder", "insured",
        "dependant", "dependent", "customer", "contact", "claimant", "beneficiary", "next of kin",
        "spouse", "employee", "staff member", "person",
    )),
]
# A heading containing one of these is about a thing, not a person ("Product name").
NOT_PERSON_QUALIFIERS = (
    "product", "plan", "scheme", "file", "hospital", "team", "company", "provider", "supplier",
    "vendor", "business", "department", "project", "task", "item", "sheet", "table", "field",
    "brand", "category", "status", "type", "document", "report", "account name", "agent name",
    "contact number", "contact email", "contact phone", "formula", "used in", "range", "tab",
    "column", "setting", "field name", "user name", "username",
)


def _norm_header(header) -> str:
    return re.sub(r"[^a-z0-9& ]+", " ", str(header or "").lower()).strip()


def classify_header(header) -> str | None:
    """Return the PII type a column heading points to, or None."""
    h = _norm_header(header)
    if not h:
        return None
    words = f" {h} "
    for pii_type, keys in HEADER_RULES:
        for k in keys:
            if f" {k} " in words or (len(k) > 4 and k in h):
                if pii_type == "PERSON" and any(q in h for q in NOT_PERSON_QUALIFIERS):
                    break
                if pii_type == "HEALTH" and "health" == k and h not in ("health", "health condition", "health issue"):
                    continue
                return pii_type
    return None


# --------------------------------------------------------------------------- text patterns

PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("EMAIL", re.compile(r"\b[\w.+'-]+@[\w-]+(?:\.[\w-]+)+\b"), "pattern"),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b"), "checksum"),
    ("CARD", re.compile(r"\b(?:\d[ -]?){12,18}\d\b"), "checksum"),
    ("PPSN", re.compile(r"\b\d{7}[A-WY][A-IW]?\b", re.IGNORECASE), "checksum"),
    ("PHONE", re.compile(
        r"(?<![\w+])(?:(?:\+|00)353[\s-]?\(?0?\)?[\s-]?[1-9]\d{0,2}|\+44[\s-]?\d{2,4}|0[1-9]\d{0,2})"
        r"[\s-]?\d{3}[\s-]?\d{3,4}\b"), "pattern"),
    ("EIRCODE", re.compile(r"\b(?:[AC-FHKNPRTV-Y]\d{2}|D6W)\s?[0-9AC-FHKNPRTV-Y]{4}\b", re.IGNORECASE), "pattern"),
    ("IP_ADDRESS", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"), "pattern"),
    ("DATE_OF_BIRTH", re.compile(
        r"(?i)\b(?:dob|d\.o\.b\.?|date of birth|born(?: on)?)\s*[:\-]?\s*"
        r"(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]+\s+\d{4})"), "pattern"),
    ("ADDRESS", re.compile(
        r"\b\d{1,4}[A-Za-z]?,?\s+(?:[A-Z][a-z'’]+\s){1,3}"
        r"(?:Road|Rd|Street|St|Avenue|Ave|Lane|Park|Drive|Close|Court|Crescent|Terrace|Grove|Way|"
        r"Place|Square|Green|Gardens|Heights|View|Hill|Lawns?|Rise|Walk|Manor|Downs|Quay|Row)\b"), "pattern"),
    ("PERSON", re.compile(rf"\b{TITLES}\.?\s+{_NAME_WORD}(?:\s+{_NAME_WORD}){{0,2}}"), "pattern"),
]


def _overlaps(f: Finding, taken: list[Finding]) -> bool:
    return any(not (f.end <= t.start or f.start >= t.end) for t in taken)


def find_in_text(text: str, member_patterns: list[re.Pattern] | None = None,
                 known: dict[str, str] | None = None, health: bool = True,
                 allow: set[str] | None = None) -> list[Finding]:
    """Find PII in free text. ``known`` maps exact strings (e.g. names seen in a Name column) to a type."""
    if not text or not isinstance(text, str):
        return []
    allow = {a.lower() for a in (allow or set())}
    found: list[Finding] = []

    def add(f: Finding):
        if f.value.strip().lower() in allow or _overlaps(f, found):
            return
        found.append(f)

    for value, ptype in sorted((known or {}).items(), key=lambda kv: -len(kv[0])):
        if len(value) < 3:
            continue
        for m in re.finditer(rf"(?<!\w){re.escape(value)}(?!\w)", text, re.IGNORECASE):
            add(Finding(ptype, m.start(), m.end(), m.group(0), "known", 0.95))

    for rx in member_patterns or []:
        for m in rx.finditer(text):
            add(Finding("MEMBER_ID", m.start(), m.end(), m.group(0), "pattern", 0.9))

    for ptype, rx, method in PATTERNS:
        for m in rx.finditer(text):
            value = m.group(0)
            if ptype == "IBAN" and not iban_valid(value):
                continue
            if ptype == "CARD" and not luhn_valid(value):
                continue
            if ptype == "PPSN" and not ppsn_valid(value):
                continue
            if ptype == "PHONE" and len(re.sub(r"\D", "", value)) < 9:
                continue
            if ptype == "DATE_OF_BIRTH":
                add(Finding(ptype, m.start(1), m.end(1), m.group(1), method, 0.9))
                continue
            add(Finding(ptype, m.start(), m.end(), value, method, 0.95 if method == "checksum" else 0.85))

    # First name from the dictionary followed by a capitalised surname-like word.
    # Lookahead so overlapping candidates are all tried ("Call Mary Byrne" -> "Mary Byrne").
    for m in re.finditer(rf"(?=\b([A-ZÁÉÍÓÚ][a-záéíóú]+)\s+({_NAME_WORD}))", text):
        first, last = m.group(1), m.group(2).strip()
        span = (m.start(1), m.end(2))
        if first in FIRST_NAMES and last not in NOT_SURNAMES:
            add(Finding("PERSON", *span, text[span[0]:span[1]], "dictionary", 0.8))
        elif last in SURNAMES and first not in NOT_SURNAMES and len(first) > 2:
            # An unknown first name before a common Irish surname ("Ailish Murphy").
            add(Finding("PERSON", *span, text[span[0]:span[1]], "dictionary", 0.7))

    if health:
        lowered = text.lower()
        for term in HEALTH_TERMS:
            for m in re.finditer(rf"(?<![\w-]){re.escape(term)}(?![\w-])", lowered):
                add(Finding("HEALTH", m.start(), m.end(), text[m.start():m.end()], "dictionary", 0.75))

    return sorted(found, key=lambda f: f.start)


def looks_like_person_name(value) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.replace(",", " ").split()
    if not 2 <= len(parts) <= 4 or any(any(ch.isdigit() for ch in p) for p in parts):
        return False
    if not all(p[0].isupper() for p in parts if p[0].isalpha()):
        return False
    return any(p.strip(".") in FIRST_NAMES or p in SURNAMES or p.startswith(NAME_PREFIXES) for p in parts)

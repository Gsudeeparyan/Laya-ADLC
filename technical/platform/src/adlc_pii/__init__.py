"""ADLC PII guard: find, remove and restore personal data in text, Excel, Word and CSV.

    from adlc_pii import scrub_file, restore_file, scrub_text
    clean_path, report, vault = scrub_file("Claims.xlsx")   # AI works on the clean copy
    print(report.text())
    restore_file("Claims (PII removed) - updated.xlsx", vault)  # real values back in the output
"""

from .detectors import ALL_TYPES, LABELS, Finding, classify_header, find_in_text, iban_valid, luhn_valid, ppsn_valid
from .policy import Policy
from .report import PiiReport
from .scrub import restore_file, scan_file, scrub_file, scrub_table, scrub_text
from .vault import TOKEN_RE, Vault

__all__ = [
    "ALL_TYPES", "LABELS", "Finding", "PiiReport", "Policy", "TOKEN_RE", "Vault", "classify_header",
    "find_in_text", "iban_valid", "luhn_valid", "ppsn_valid", "restore_file", "scan_file", "scrub_file",
    "scrub_table", "scrub_text",
]

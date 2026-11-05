"""The vault: which token stands for which real value.

The same real value always gets the same token (PERSON_001 every time "Mary Byrne"
appears), so counts, joins and grouping still work on the cleaned data. The vault is
what lets real values be put back into an output file later.

The vault itself contains the PII. Keep it next to the original file, in a restricted
location. Never upload it to an AI tool.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from .detectors import ALL_TYPES

TOKEN_RE = re.compile(r"\b(" + "|".join(ALL_TYPES) + r")_(\d{3,})\b")
_DIGITS_ONLY = {"PHONE", "CARD", "IBAN", "PPSN", "BANK_ACCOUNT", "PASSPORT"}


def _key(ptype: str, value) -> str:
    text = value.isoformat() if isinstance(value, (date, datetime)) else str(value)
    if ptype in _DIGITS_ONLY:
        return re.sub(r"[^0-9A-Za-z]", "", text).upper()
    return re.sub(r"\s+", " ", text).strip().lower()


def _encode(value):
    if isinstance(value, datetime):
        return {"kind": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"kind": "date", "value": value.isoformat()}
    if isinstance(value, bool):
        return {"kind": "str", "value": str(value)}
    if isinstance(value, int):
        return {"kind": "int", "value": value}
    if isinstance(value, float):
        return {"kind": "float", "value": value}
    return {"kind": "str", "value": str(value)}


def _decode(entry):
    kind, value = entry["kind"], entry["value"]
    if kind == "datetime":
        return datetime.fromisoformat(value)
    if kind == "date":
        return date.fromisoformat(value)
    return value


def display(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y") if value.time() == datetime.min.time() else value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


class Vault:
    def __init__(self, source: str = ""):
        self.source = source
        self.tokens: dict[str, dict] = {}
        self._index: dict[tuple[str, str], str] = {}
        self._counters: dict[str, int] = {}

    def token_for(self, ptype: str, value) -> str:
        key = (ptype, _key(ptype, value))
        if key in self._index:
            return self._index[key]
        self._counters[ptype] = self._counters.get(ptype, 0) + 1
        token = f"{ptype}_{self._counters[ptype]:03d}"
        while token in self.tokens:  # tokens loaded from an older vault
            self._counters[ptype] += 1
            token = f"{ptype}_{self._counters[ptype]:03d}"
        self.tokens[token] = {"type": ptype, **_encode(value)}
        self._index[key] = token
        return token

    def original(self, token: str):
        entry = self.tokens.get(token)
        return None if entry is None else _decode(entry)

    def restore_text(self, text: str) -> str:
        if not isinstance(text, str):
            return text

        def sub(m):
            entry = self.tokens.get(m.group(0))
            return display(_decode(entry)) if entry else m.group(0)

        return TOKEN_RE.sub(sub, text)

    def restore_value(self, value):
        """Whole-cell token -> original typed value; tokens inside text -> text with originals."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped in self.tokens:
                return _decode(self.tokens[stripped])
            return self.restore_text(value)
        return value

    def retokenise_text(self, text: str) -> str:
        """Replace any real value held in this vault with its token (longest first)."""
        if not isinstance(text, str) or not self.tokens:
            return text
        pairs = sorted(((display(_decode(e)), t) for t, e in self.tokens.items()), key=lambda p: -len(p[0]))
        for original, token in pairs:
            if len(original) >= 3:
                text = re.sub(rf"(?<!\w){re.escape(original)}(?!\w)", token, text, flags=re.IGNORECASE)
        return text

    def detokenise(self, obj):
        """Swap tokens for real values anywhere inside dicts, lists and strings (typed where possible)."""
        if isinstance(obj, dict):
            return {k: self.detokenise(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.detokenise(v) for v in obj]
        return self.restore_value(obj) if isinstance(obj, str) else obj

    def __len__(self):
        return len(self.tokens)

    # ------------------------------------------------------------------ persistence

    def to_dict(self) -> dict:
        return {
            "adlc_pii_vault": 1,
            "warning": "Contains personal data. Keep with the original file. Never upload to an AI tool.",
            "source": self.source,
            "created": datetime.now().replace(microsecond=0).isoformat(),
            "tokens": self.tokens,
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=1, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, data: dict) -> "Vault":
        v = cls(data.get("source", ""))
        for token, entry in data.get("tokens", {}).items():
            v.tokens[token] = entry
            v._index[(entry["type"], _key(entry["type"], _decode(entry)))] = token
            ptype, num = token.rsplit("_", 1)
            v._counters[ptype] = max(v._counters.get(ptype, 0), int(num))
        return v

    @classmethod
    def load(cls, path: str | Path) -> "Vault":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

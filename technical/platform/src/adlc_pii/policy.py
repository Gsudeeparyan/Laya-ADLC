"""What to do with each kind of PII.

Two built-in profiles:

  restore    (default) Direct identifiers become tokens (PERSON_001). The AI works on
             tokens; real values can be put back into the output file with the vault.
             Health details are kept (they are the point of most tasks) but reported,
             and nothing in the cleaned file links them to a person.
  anonymise  For sharing or analysis: identifiers are removed for good, dates of birth
             become a year of birth, Eircodes keep only the area (routing key).

Actions: pseudonymise | redact | generalise | keep. Laya can override any of this in
config/pii-policy.yaml (also where Laya's member/policy/claim number formats go).
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

import yaml

from .detectors import DIRECT

ACTIONS = ("pseudonymise", "redact", "generalise", "keep")

DEFAULT_POLICY = {
    "profiles": {
        "restore": {**{t: "pseudonymise" for t in DIRECT}, "DATE_OF_BIRTH": "pseudonymise",
                    "HEALTH": "keep", "STAFF_NAME": "keep"},
        "anonymise": {**{t: "redact" for t in DIRECT}, "DATE_OF_BIRTH": "generalise",
                      "EIRCODE": "generalise", "HEALTH": "keep", "STAFF_NAME": "pseudonymise"},
    },
    "member_id_patterns": [],
    "allow_list": ["Laya", "Laya Healthcare", "laya healthcare"],
}


class Policy:
    def __init__(self, data: dict | None = None, profile: str = "restore"):
        merged = copy.deepcopy(DEFAULT_POLICY)
        for key, value in (data or {}).items():
            if key == "profiles":
                for name, actions in value.items():
                    merged["profiles"].setdefault(name, {}).update(actions)
            else:
                merged[key] = value
        if profile not in merged["profiles"]:
            raise ValueError(f"Unknown PII profile '{profile}'. Known: {', '.join(merged['profiles'])}")
        self.profile = profile
        self.actions: dict[str, str] = merged["profiles"][profile]
        bad = {t: a for t, a in self.actions.items() if a not in ACTIONS}
        if bad:
            raise ValueError(f"Unknown PII actions: {bad}. Use one of {', '.join(ACTIONS)}.")
        self.member_patterns = [re.compile(p["regex"]) for p in merged.get("member_id_patterns", []) if p.get("regex")]
        self.allow = set(merged.get("allow_list", []))

    def action(self, ptype: str) -> str:
        return self.actions.get(ptype, "pseudonymise")

    @property
    def restorable(self) -> bool:
        return all(a in ("pseudonymise", "keep") for a in self.actions.values())

    @classmethod
    def load(cls, path: str | Path | None = None, profile: str = "restore") -> "Policy":
        candidates = [Path(path)] if path else [Path("config/pii-policy.yaml")]
        for p in candidates:
            if p.exists():
                return cls(yaml.safe_load(p.read_text(encoding="utf-8")) or {}, profile)
        return cls(None, profile)

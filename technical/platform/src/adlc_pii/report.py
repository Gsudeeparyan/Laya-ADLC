"""PII report: what was found, where, and what was done - in plain English."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

from .detectors import DIRECT, LABELS, SPECIAL
from .vault import display

ACTION_WORDS = {
    "pseudonymise": "replaced with tokens (real values can be put back)",
    "redact": "removed",
    "generalise": "reduced to a broad value (e.g. year of birth, area code)",
    "keep": "kept, but flagged",
}


def mask(value) -> str:
    s = display(value).strip()
    if len(s) <= 3:
        return s[:1] + "**"
    if len(s) <= 6:
        return s[:1] + "***" + s[-1:]
    return s[:2] + "***" + s[-2:]


@dataclass
class Location:
    where: str
    type: str
    count: int
    method: str
    example: str
    action: str


class PiiReport:
    def __init__(self, source: str = ""):
        self.source = source
        self._locations: dict[tuple[str, str], Location] = {}

    def add(self, where: str, ptype: str, method: str, value, action: str, n: int = 1):
        key = (where, ptype)
        loc = self._locations.get(key)
        if loc is None:
            self._locations[key] = Location(where, ptype, n, method, mask(value), action)
        else:
            loc.count += n

    @property
    def locations(self) -> list[Location]:
        return sorted(self._locations.values(), key=lambda l: (-l.count, l.where))

    @property
    def counts(self) -> Counter:
        c = Counter()
        for loc in self._locations.values():
            c[loc.type] += loc.count
        return c

    @property
    def risk(self) -> str:
        """none | low (staff names only) | personal | special (health data alongside identifiers)."""
        types = set(self.counts)
        if not types:
            return "none"
        if types & set(SPECIAL) and types & set(DIRECT + ("DATE_OF_BIRTH",)):
            return "special"
        if types & set(SPECIAL):
            return "personal"
        if types <= {"STAFF_NAME"}:
            return "low"
        return "personal"

    def summary_lines(self) -> list[str]:
        lines = []
        for ptype, n in self.counts.most_common():
            places = sorted({l.where for l in self._locations.values() if l.type == ptype})
            where = ", ".join(places[:4]) + (f" and {len(places) - 4} more" if len(places) > 4 else "")
            lines.append(f"{n} x {LABELS.get(ptype, ptype)} - in {where}")
        return lines

    def text(self, cleaned: bool = True) -> str:
        if self.risk == "none":
            return f"No personal data found in {self.source or 'this content'}."
        head = {
            "low": "Contains staff names only (low risk).",
            "personal": "Contains personal data.",
            "special": "Contains personal data AND health information (special category data - highest care).",
        }[self.risk]
        out = [f"PII check: {self.source}".strip(), head, "", "Found:"]
        out += [f"  - {line}" for line in self.summary_lines()]
        if cleaned:
            done = {}
            for loc in self._locations.values():
                done.setdefault(loc.action, set()).add(LABELS.get(loc.type, loc.type))
            out += ["", "What was done:"]
            out += [f"  - {', '.join(sorted(types))}: {ACTION_WORDS.get(action, action)}" for action, types in done.items()]
        return "\n".join(out)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "risk": self.risk,
            "counts": dict(self.counts),
            "locations": [asdict(l) for l in self.locations],
        }

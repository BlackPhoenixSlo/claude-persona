#!/usr/bin/env python3
"""Parse a plain-text DMCA takedown notice into structured data.

Usage:
    python3 dmca_notice_parser.py <notice.txt>

Prints a JSON object to stdout. Pure stdlib, best-effort heuristics.
"""

import datetime
import json
import re
import sys

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

URL_RE = re.compile(r"""https?://[^\s<>"'`]+""", re.IGNORECASE)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Trailing characters that are almost never part of a URL in prose.
# (`<>"'` cannot occur here: URL_RE already excludes them from the match.)
URL_TRAILING = ".,;:!?)]}*"

NAME_LABEL_RE = re.compile(
    r"^\s*(claimant name|claimant|name|from)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
# Lower number == higher priority when several labels are present.
NAME_LABEL_PRIORITY = {
    "claimant name": 0,
    "claimant": 0,
    "name": 1,
    "from": 2,
}

EMAIL_LABEL_RE = re.compile(
    r"^\s*(e-?mail address|e-?mail)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)

SIGNOFF_RE = re.compile(
    r"^\s*(sincerely|regards|best regards|kind regards|respectfully|"
    r"thank you|thanks|yours truly|yours sincerely)\s*[,.]?\s*$",
    re.IGNORECASE,
)
SLASH_S_RE = re.compile(r"^\s*/s/\s*(.+?)\s*$", re.IGNORECASE)

DATE_LABEL_RE = re.compile(r"^\s*(date|dated|date of notice)\s*:\s*(.+?)\s*$", re.IGNORECASE)

# Section cues. Every occurrence in a line is recorded; each URL takes the
# bucket of the last cue that precedes it (see ``_extract_urls``).
INFRINGING_CUES = (
    "infring",  # stem: infringing / infringed / infringement
    "located at",
    "unauthorized cop",
    "takedown",
)
ORIGINAL_CUES = (
    "original work",
    "copyrighted work",
    "authorized cop",
    "original url",
)
CUE_RE = re.compile(
    "(?P<infringing>" + "|".join(INFRINGING_CUES) + ")"
    "|(?P<original>" + "|".join(ORIGINAL_CUES) + ")",
    re.IGNORECASE,
)

MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))

ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")
MONTH_FIRST_RE = re.compile(
    r"\b(" + _MONTH_ALT + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s+(\d{4})\b",
    re.IGNORECASE,
)
DAY_FIRST_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + _MONTH_ALT + r")\.?\s*,?\s+(\d{4})\b",
    re.IGNORECASE,
)
SLASH_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_url(raw):
    """Strip trailing prose punctuation from a captured URL."""
    url = raw.strip()
    while url and url[-1] in URL_TRAILING:
        url = url[:-1]
    return url


def _dedupe(urls):
    seen = set()
    out = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _clean_name(value):
    """Normalise a candidate name; return None if it does not look like one."""
    name = value.strip()
    if "<" in name:
        name = name.split("<", 1)[0]
    name = name.strip().strip('"').strip("'").strip()
    name = name.rstrip(",;:")
    if not name or len(name) > 80:
        return None
    lowered = name.lower()
    if "http" in lowered or "@" in name:
        return None
    if not re.search(r"[A-Za-z]", name):
        return None
    return name


def _extract_name(lines):
    best = None  # (priority, name)
    for line in lines:
        match = NAME_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower()
        name = _clean_name(match.group(2))
        if name is None:
            continue
        priority = NAME_LABEL_PRIORITY[label]
        if best is None or priority < best[0]:
            best = (priority, name)
    if best is not None:
        return best[1]

    # Signature fallbacks.
    for index, line in enumerate(lines):
        if SIGNOFF_RE.match(line):
            for candidate in lines[index + 1:index + 3]:
                slash_s = SLASH_S_RE.match(candidate)
                if slash_s:
                    candidate = slash_s.group(1)
                name = _clean_name(candidate)
                if name:
                    return name
    for line in lines:
        match = SLASH_S_RE.match(line)
        if match:
            name = _clean_name(match.group(1))
            if name:
                return name
    return None


def _extract_email(lines):
    for line in lines:
        match = EMAIL_LABEL_RE.match(line)
        if match:
            found = EMAIL_RE.search(match.group(2))
            if found:
                return found.group(0)
    for line in lines:
        match = NAME_LABEL_RE.match(line)
        if match and match.group(1).lower() == "from":
            found = EMAIL_RE.search(match.group(2))
            if found:
                return found.group(0)
    return None


def _line_cues(line):
    """Return ``[(offset, 'infringing'|'original'), ...]`` for one line."""
    return [(match.start(), match.lastgroup) for match in CUE_RE.finditer(line)]


def _extract_urls(lines):
    infringing = []
    original = []
    # URLs seen before any cue default to the infringing bucket: it is the
    # dominant one in real notices.
    current = "infringing"
    for line in lines:
        cues = _line_cues(line)
        for match in URL_RE.finditer(line):
            preceding = [bucket for offset, bucket in cues if offset < match.start()]
            if preceding:
                bucket = preceding[-1]
            elif cues:
                # No cue to the left: fall back to the nearest one to the right.
                bucket = cues[0][1]
            else:
                bucket = current
            if bucket == "original":
                original.append(_clean_url(match.group(0)))
            else:
                infringing.append(_clean_url(match.group(0)))
        if cues:
            current = cues[-1][1]
    return _dedupe(infringing), _dedupe(original)


def _to_iso(year, month, day):
    try:
        return datetime.date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _parse_date_text(text):
    """Return the first ISO date found in ``text``, or None."""
    candidates = []
    for match in ISO_DATE_RE.finditer(text):
        candidates.append((match.start(), match.group(1), match.group(2), match.group(3)))
    for match in MONTH_FIRST_RE.finditer(text):
        month = MONTHS[match.group(1).lower()]
        candidates.append((match.start(), match.group(3), month, match.group(2)))
    for match in DAY_FIRST_RE.finditer(text):
        month = MONTHS[match.group(2).lower()]
        candidates.append((match.start(), match.group(3), month, match.group(1)))
    for match in SLASH_DATE_RE.finditer(text):
        # Assume US-style MM/DD/YYYY.
        candidates.append((match.start(), match.group(3), match.group(1), match.group(2)))

    for _, year, month, day in sorted(candidates, key=lambda item: item[0]):
        iso = _to_iso(year, month, day)
        if iso:
            return iso
    return None


def _extract_date(lines, text):
    for line in lines:
        match = DATE_LABEL_RE.match(line)
        if match:
            iso = _parse_date_text(match.group(2))
            if iso:
                return iso
    # Fall back to the whole document, with URLs removed so that paths such as
    # /2026/02/ cannot be mistaken for dates.
    return _parse_date_text(URL_RE.sub(" ", text))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_notice(text):
    """Parse a DMCA notice and return a dict of extracted fields."""
    lines = text.splitlines()
    infringing_urls, original_work_urls = _extract_urls(lines)
    return {
        "claimant_name": _extract_name(lines),
        "claimant_email": _extract_email(lines),
        "infringing_urls": infringing_urls,
        "original_work_urls": original_work_urls,
        "date": _extract_date(lines, text),
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 dmca_notice_parser.py <notice.txt>\n")
        return 1
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
            text = handle.read()
    except OSError as exc:
        sys.stderr.write("error: cannot read %s: %s\n" % (path, exc.strerror or exc))
        return 1
    print(json.dumps(parse_notice(text), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

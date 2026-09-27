# dmca-notice-parser

A small parser that turns a plain-text DMCA takedown notice into structured
JSON. No runtime dependencies (Python 3 stdlib only); tests need `pytest`.

## Usage

```bash
python3 dmca_notice_parser.py samples/notice1.txt
```

Example output:

```json
{
  "claimant_name": "Marguerite Delacroix-Ferris",
  "claimant_email": "mdelacroix@example.org",
  "infringing_urls": [
    "http://cdn.example.net/uploads/2026/atlas-chapter-one.pdf",
    "http://cdn.example.net/uploads/2026/atlas-chapter-two.pdf",
    "http://mirror.example.net/files/atlas-chapter-one.pdf"
  ],
  "original_work_urls": [
    "https://www.example.org/catalog/atlas-of-forgotten-rivers",
    "https://www.example.org/catalog/atlas-of-forgotten-rivers/preview"
  ],
  "date": "2026-03-05"
}
```

As a library:

```python
from dmca_notice_parser import parse_notice

result = parse_notice(open("notice.txt", encoding="utf-8-sig").read())
```

Exit codes: `0` on success, `1` if the file is missing/unreadable or if the
argument count is wrong (message on stderr, nothing on stdout).

## Output schema

| Key                  | Type              | Notes                                          |
| -------------------- | ----------------- | ---------------------------------------------- |
| `claimant_name`      | `str` or `null`   | From labelled fields or the signature block    |
| `claimant_email`     | `str` or `null`   | First plausible sender address                 |
| `infringing_urls`    | `list[str]`       | Order preserved, deduplicated; `[]` if none    |
| `original_work_urls` | `list[str]`       | Order preserved, deduplicated; `[]` if none    |
| `date`               | `str` or `null`   | ISO `YYYY-MM-DD`                               |

Every field is best-effort: missing data yields `null` or `[]`. `parse_notice`
takes a `str` and is not expected to raise on arbitrary text; it is heuristic
code, not a hardened parser, so treat unexpected exceptions as bugs.

## How it works (heuristics)

- **Name**: labelled fields in priority order — `Claimant:` / `Claimant Name:`,
  `Name:`, `From:` — falling back to the line after a sign-off (`Sincerely,`,
  `Regards,` ...) or an `/s/ Name` line. Angle-bracket addresses are stripped
  from `From:` values.
- **Email**: `Email:` / `E-mail:` / `E-mail address:` first, then the `From:`
  header. Addresses in unlabelled prose are not collected.
- **URLs**: lines are scanned top to bottom while tracking the "current section".
  Cues such as `infring*` (`infringing`, `infringed`, `infringement`),
  `located at`, `unauthorized copies`, `takedown` switch to the infringing
  bucket; `Original work`, `Copyrighted work`, `authorized copies`,
  `Original URL` switch to the original-work bucket. Each `http(s)` URL is
  assigned per URL, not per line: it takes the bucket of the last cue occurring
  *before* it on the same line, otherwise the first cue *after* it on that line,
  otherwise the current (sticky) section.
  Trailing prose punctuation (`. , ; : ) ]` ...) is stripped. The section is
  sticky until the next cue, so blank lines and bullet lists work.
- **Date**: the `Date:` / `Dated:` field first, otherwise the earliest date-like
  string in the document (URLs are removed first so paths like `/2026/02/`
  are not mistaken for dates). Accepted: `YYYY-MM-DD`, `March 5, 2026`,
  `5 March 2026`, `MM/DD/YYYY`.

## Limitations

- Slash dates are assumed to be US-style `MM/DD/YYYY`; `05/03/2026` parses as
  3 May, not 5 March.
- URLs that appear before any section cue are assumed to be infringing.
- If a single line contains both an infringing and an original-work cue, each
  URL follows the nearest cue to its left (or, with no cue to its left, the
  nearest one to its right), so one line can feed both buckets.
- Only the first matching value is returned for name/email/date; multiple
  claimants or contact addresses are not modelled.
- Bare hostnames (`example.net/path` without a scheme), FTP links, and
  non-English notices are not recognised.
- No validation of legal completeness (good-faith statement, perjury clause,
  signature) is performed.

## Tests

```bash
python3 -m pytest -q
```

Run from the repository root. `samples/` holds three fictitious notices used as
fixtures.

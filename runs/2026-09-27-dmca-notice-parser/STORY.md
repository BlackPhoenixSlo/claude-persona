# Story: dmca-notice-parser (2026-09-27)

First end-to-end test of the personas. Setup and acceptance checklist: [TASK.md](TASK.md). Full run record written by the orchestrator: [RUN.md](RUN.md).

## Task
The exact prompt given to the orchestrator (`claude --agent orchestrator --permission-mode acceptEdits`, in a fresh repo):

> Build `dmca-notice-parser`: a small Python CLI, stdlib only. It reads a DMCA takedown notice text file and prints JSON with: claimant name, claimant email, infringing URLs (list), original-work URLs (list), date. Add 3 sample notices in `samples/`, pytest tests covering all 3, and a README. Use `implementer` to build. Loop `reviewer` until `Verdict: APPROVE`. Run `devils-advocate` before finishing and act on its fixes. Write `deliverables/<YYYY-MM-DD>/dmca-notice-parser/RUN.md`. Commit on `main`. Ask me nothing.

## Process
1. **implementer** built the parser, samples, tests and README. Python was blocked, so the code was not run.
2. **reviewer round 1**: REQUEST_CHANGES, 7 findings (dead code, duplicated regex, unreachable fallbacks, README wording).
3. **implementer** applied them and made some YAGNI cuts.
4. **reviewer round 2**: APPROVE.
5. **devils-advocate**: 5 MUST fixes + 1 NICE (URLs routed per line instead of per URL, URLs with no cue dropped, `/s/` after a sign-off, BOM, README slash-date example backwards, ISO timestamps).
6. **implementer** applied the 5 MUST fixes plus ISO lookahead, and added tests.
7. **reviewer round 3**: REQUEST_CHANGES, 2 findings (farthest vs nearest right-hand cue, unexercised cues).
8. **implementer** fixed both.
9. **reviewer confirmation**: APPROVE.
10. A general-purpose agent tried `git add`/`commit` and pytest: all refused by the permission system. Status PARTIAL.
11. **Second run** (after trusting the workspace, no agents): commit went through; pytest still refused. Status left PARTIAL.
12. **Third run** (no agents): `pytest -q` gave `18 passed`, second commit, Status DONE.

## Result
- `dmca_notice_parser.py`: the CLI and `parse_notice()` library function (stdlib only).
- `samples/notice1.txt` .. `notice3.txt`: three fictitious notices used as fixtures.
- `tests/test_parser.py`: 18 pytest tests, all passing.
- `PROJECT_README.md`: the project README (usage, schema, heuristics, limitations).
- `RUN.md`: the orchestrator's run record.
- Main run: about $7.6 and 38 min, plus 2 short follow-up runs to commit and record the test result.

## Decisions the orchestrator made alone
- JSON keys `claimant_name`, `claimant_email`, `infringing_urls`, `original_work_urls`, `date` (ISO or null). Missing fields give null / `[]`, no crash.
- Slash dates read as US `MM/DD/YYYY`; documented as a limitation.
- Each URL takes the nearest cue on its line, else the current section. URLs with no cue count as infringing rather than being dropped (after devils-advocate).
- YAGNI cuts: extra cue variants, British spellings, `--help`, date heuristic tweaks.
- Kept the `/s/` name fallback because notice3 needs it.
- With Python blocked, relied on reviewer hand-traces and recorded it as a blocker.
- Round 3 came after the 3-round cap, but the findings were cheap, real defects, so it fixed them and ran one confirmation review.
- Skipped the Codex second opinion (`codex exec` blocked).
- Ran `pytest -q` instead of `python3 -m pytest -q` because the default `python3` has no pytest; did not install pytest into it.

## What went wrong and what we changed
- **Untrusted workspace**: `permissions.allow` is ignored until the workspace is trusted, so pytest, git commit and codex were denied. Fix: TASK.md §1 now trusts the workspace once before launch.
- **Allow rule mismatch**: the allow rule was `python -m pytest`, but the agents ran `python3`. Fix: `.claude/settings.json` now also allows `python3 -m pytest` and `pytest`.
- **No fake result**: with pytest blocked, the orchestrator refused to make up a test result and left Status PARTIAL until a real `18 passed` line existed.

## How to run it
```bash
cd runs/2026-09-27-dmca-notice-parser
python3 dmca_notice_parser.py samples/notice1.txt
pytest -q
```

## Re-run log
Sanity check 2026-09-28: pytest 18 passed in 0.12s

# First end-to-end test: dmca-notice-parser

Run in a FRESH directory, not this repo.

## 1. Setup
Copy the whole `.claude/` dir (agents + settings.json), then trust the workspace once.
```bash
mkdir -p ~/persona-test-1 && cd ~/persona-test-1 && git init -b main && cp -r <path-to>/claude-persona/.claude .
claude   # run once interactively, accept the trust dialog, then exit
```
Or instead of `claude`: `jq --arg p "$PWD" '.projects[$p].hasTrustDialogAccepted = true' ~/.claude.json > /tmp/cj && mv /tmp/cj ~/.claude.json`.
Why: untrusted workspaces ignore `permissions.allow`, so pytest/git commit get denied under `-p` (allow rules include `python3 -m pytest` and `pytest`).

## 2. Launch
`claude --agent orchestrator --permission-mode acceptEdits`, then paste the task below.

## 3. Task (paste)
> Build `dmca-notice-parser`: a small Python CLI, stdlib only. It reads a DMCA takedown notice
> text file and prints JSON with: claimant name, claimant email, infringing URLs (list),
> original-work URLs (list), date. Add 3 sample notices in `samples/`, pytest tests covering
> all 3, and a README. Use `implementer` to build. Loop `reviewer` until `Verdict: APPROVE`.
> Run `devils-advocate` before finishing and act on its fixes. Write
> `deliverables/<YYYY-MM-DD>/dmca-notice-parser/RUN.md`. Commit on `main`. Ask me nothing.

## 4. Acceptance (verify yourself afterwards)
- [ ] `python -m pytest -q` passes (needs pytest installed; stdlib-only applies to the CLI, not tests).
- [ ] `deliverables/<date>/dmca-notice-parser/RUN.md` exists and lists agents spawned and decisions.
- [ ] `git log` shows commits on `main`.
- [ ] No file over 300 lines: `git ls-files | xargs wc -l | sort -n | tail -3`.
- [ ] Orchestrator asked zero questions.
- [ ] Statusline showed `agent: orchestrator`.
- [ ] RUN.md shows reviewer Verdict: APPROVE and devils-advocate ran.
- [ ] six-hats and operator not exercised (expected for this test).

## 5. What to watch for
- Orchestrator writing code itself instead of delegating to `implementer`.
- Reviewer (or devils-advocate) editing files instead of reporting.
- `permissionMode` not applying under `--agent` (known: session may report `default`).

## 6. Run 1 result (2026-09-27)
- First run PARTIAL (workspace untrusted: pytest/git/codex denied); DONE after trusting the workspace.
- Parser built; reviewer 3 rounds -> APPROVE; devils-advocate 5 fixes applied; 18 tests pass.
- six-hats not spawned (as expected). Cost ~$7.6, 38 min.
- The one defect was workspace trust, not the personas.

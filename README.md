# claude-persona

Six Claude Code personas (orchestrator, reviewer, implementer, devils-advocate, six-hats, operator), one `.claude/agents/<name>.md` file each, plus a deny baseline and statusline in `.claude/settings.json`.

## Quick start

```bash
git clone https://github.com/TheCodeDestroyer/claude-persona.git
mkdir -p <your-repo>/.claude && cp -r claude-persona/.claude/. <your-repo>/.claude/
cd <your-repo> && claude   # once: accept the trust dialog, then exit
claude --agent orchestrator --permission-mode acceptEdits "<task>"
```

The `--permission-mode` flag is required: frontmatter `permissionMode` is ignored under `--agent`. `claude --agent <name>` runs any persona for the whole session. Mid-session, type `@agent-reviewer` (or pick `reviewer (agent)` from the @ menu) to delegate to it.

The orchestrator writes a run record to `deliverables/YYYY-MM-DD/<slug>/RUN.md` (ask, decisions, agents, results, cuts) in your repo.

## Personas

Pick a persona explicitly. The descriptions only discourage auto-delegation; Claude Code can still delegate on its own.

| Name | Model / effort | What it does | Enforced / advisory |
|------|----------------|--------------|---------------------|
| orchestrator | inherit / medium | Drives the task to completion via Opus subagents; tools `Agent, Read, Grep, Glob, Bash, Write`, `acceptEdits` | Tool list enforced; "delegate, don't build" advisory |
| reviewer | opus / high | Strict read-only review, APPROVE / REQUEST CHANGES; tools `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; git-only Bash scope advisory |
| implementer | opus / high | Makes the change, reports validation; tools `Read, Edit, Write, Grep, Glob, Bash`, `acceptEdits` | Tool list enforced; body advisory |
| devils-advocate | opus / high | Read-only critic that argues against the work; tools `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; git-only Bash advisory |
| six-hats | opus / high | Read-only de Bono six thinking hats; tools `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; git-only Bash advisory |
| operator | opus / high | Operates browser and desktop apps; tools `Read, Glob, Grep` + Chrome / browser / computer-use MCP, `default` | Tool list enforced; "no credentials/sends" advisory |

## What is enforced

- **Deny rules** (`permissions.deny`): `rm -rf`/`-fr`/`-r`/`-R`, `git push --force`/`-f`, reading `.env*`, `**/secrets/**`, `~/.ssh/**`. These are the only rules enforced everywhere.
- **Allow rules** (`permissions.allow`): git status/diff/log/add/commit, `python -m pytest`, `python3 -m pytest`, `pytest`, `codex exec`.
- **Statusline:** shows `agent: <name>`, or `agent: default` without `--agent` (`@`-delegation still shows default). Needs `jq` installed.

These are guardrails, not a sandbox.

## Caveats

- `permissionMode` was observed not to apply under `claude -p --agent` (session reported `default`). It applies when the persona runs as a subagent via `@agent-<name>`, and a parent in `bypassPermissions`, `acceptEdits` or `auto` overrides it.
- `tools:` limits the whole session under `claude --agent <name>`. With `@`-delegation it limits only the subagent, not your main thread.
- Bash denies are prefix matches. They miss `git push origin main --force`, `rm -f -r`, `rm --recursive`, `sh -c ...` and full-path binaries such as `/bin/rm`.
- Read denies also cover `cat`/`head`/`tail`/`sed` in Bash, but not `grep -r`, scripts (python/node) or `< .env` redirects.
- Grep/Glob were absent from the session tool list under `claude -p --agent` when Bash was also listed (2.1.252); Bash equivalents still work.
- A fresh workspace must be trusted once (interactive `claude`, or `hasTrustDialogAccepted` in `~/.claude.json`); otherwise `permissions.allow` is ignored and `-p` runs get denied on pytest/git.
- Permission arrays merge. Overlays can add denies but cannot remove allows.
- operator: browser/computer MCP tools under `--agent` are untested. Computer use is off until enabled in `/mcp` and does not work under `claude -p`; Chrome needs `claude --chrome`.

## Verify

```bash
claude --agent reviewer
# then ask: "rm -rf /tmp/x" and "read .env"  -> both must be refused
```

Smoke test (2026-09-27, `claude -p --agent reviewer`): Read `.env` blocked by deny rule; Edit absent from tool list; `rm -rf`/`cat .env` refused by the model before any tool call (Bash denies not exercised); `permissionMode: plan` not applied (session reported `default`).

## First end-to-end test

[TEST_PROJECT.md](TEST_PROJECT.md) builds a small Python CLI in a fresh repo with the orchestrator, implementer, reviewer and devils-advocate. Result on 2026-09-27: 18 tests pass, reviewer approved after 3 rounds, ~$7.6, 38 min. The only defect was workspace trust, not the personas.

## Sharing

Commit `.claude/` to share with your team. Copy the agent files to `~/.claude/agents/` for personal use.

Tested with Claude Code 2.1.252. Design decisions: [PLAN.md](PLAN.md).

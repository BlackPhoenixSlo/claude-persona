# claude-persona

Six Claude Code personas, one `.claude/agents/<name>.md` file each. Pick a persona explicitly. The descriptions only discourage auto-delegation; Claude Code can still delegate on its own.

| Name | Model | Tools | Enforced / advisory |
|------|-------|-------|---------------------|
| orchestrator | inherit, effort medium | `Agent, Read, Grep, Glob, Bash, Write`, `acceptEdits` | Tool list enforced; "delegate, don't build" advisory |
| reviewer | opus, effort high | `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; body (incl. git-only Bash scope) advisory |
| implementer | opus, effort high | `Read, Edit, Write, Grep, Glob, Bash`, `acceptEdits` | Tool list enforced; body advisory |
| devils-advocate | opus, effort high | `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; git-only Bash advisory |
| six-hats | opus, effort high | `Read, Grep, Glob, Bash`, `plan` | Tool list enforced; git-only Bash advisory |
| operator | opus, effort high | `Read, Glob, Grep` + Chrome / browser / computer-use MCP, `default` | Tool list enforced; "no credentials/sends" advisory |

`permissionMode` was observed not to apply under `claude -p --agent` (session reported `default`); it applies when the persona runs as a subagent via `@agent-reviewer`, and a parent in `bypassPermissions`, `acceptEdits` or `auto` overrides it. Only the `permissions.deny` rules in `.claude/settings.json` are enforced everywhere.

**Launch:** `claude --agent orchestrator --permission-mode acceptEdits "<task>"` is the main entry (the flag is required: frontmatter permissionMode is ignored under --agent); `claude --agent <name>` runs any persona for the whole session. `@agent-reviewer` (or pick `reviewer (agent)` from the @ menu) delegates to it mid-session.

**Run record:** the orchestrator writes `deliverables/YYYY-MM-DD/<slug>/RUN.md` (ask, decisions, agents, results, cuts) in the project repo.

**Verify:** under `claude --agent reviewer`, ask Claude to `rm -rf /tmp/x` and to read `.env`. Both must be refused.
Smoke test (2026-09-27, `claude -p --agent reviewer`): Read `.env` blocked by deny rule; Edit absent from tool list; `rm -rf`/`cat .env` refused by the model before any tool call (Bash denies not exercised); `permissionMode: plan` not applied (session reported `default`).

**Caveats**
- Pattern denies are guardrails, not a sandbox.
- Bash denies are prefix matches. They miss `git push origin main --force`, `rm -f -r`, `rm --recursive`, `sh -c ...` and full-path binaries such as `/bin/rm`.
- Read denies also cover `cat`/`head`/`tail`/`sed` in Bash, but not `grep -r`, scripts (python/node) or `< .env` redirects.
- `tools:` limits the whole session under `claude --agent <name>`. With `@`-delegation it limits only the subagent, not your main thread.
- Grep/Glob were absent from the session tool list under `claude -p --agent` when Bash was also listed (2.1.252); Bash equivalents still work.
- A fresh workspace must be trusted once (interactive `claude` or `hasTrustDialogAccepted` in ~/.claude.json) or `permissions.allow` is ignored and `-p` runs get denied on pytest/git.
- Permission arrays merge. Overlays can add denies but cannot remove allows.
- operator: browser/computer MCP tools under `--agent` are untested. Computer use is off until enabled in `/mcp` and does not work under `claude -p`; Chrome needs `claude --chrome`.

**Statusline:** shows `agent: <name>`, or `agent: default` without `--agent` (`@`-delegation still shows default). It uses jq, so jq must be installed.

**Sharing:** commit `.claude/` to share with the team. Copy the agent files to `~/.claude/agents/` for personal use.

Tested with Claude Code 2.1.252.

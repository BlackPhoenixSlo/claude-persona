# claude-persona

Two Claude Code personas, one `.claude/agents/<name>.md` file each. Pick a persona explicitly. The descriptions only discourage auto-delegation; Claude Code can still delegate on its own.

| Name | Model | Tools | Enforced / advisory |
|------|-------|-------|---------------------|
| reviewer | opus | `Read, Grep, Glob, Bash`, `permissionMode: plan` | Tool list enforced; body (incl. git-only Bash scope) advisory |
| implementer | sonnet | `Read, Edit, Write, Grep, Glob, Bash`, `permissionMode: acceptEdits` | Tool list enforced; body advisory |

`permissionMode` was observed not to apply under `claude -p --agent` (session reported `default`); it applies when the persona runs as a subagent via `@agent-reviewer`, and a parent in `bypassPermissions`, `acceptEdits` or `auto` overrides it. Only the `permissions.deny` rules in `.claude/settings.json` are enforced everywhere.

**Launch:** `claude --agent reviewer` runs the whole session as the persona. `@agent-reviewer` (or pick `reviewer (agent)` from the @ menu) delegates to it mid-session.

**Verify:** under `claude --agent reviewer`, ask Claude to `rm -rf /tmp/x` and to read `.env`. Both must be refused.
Smoke test (2026-09-27, `claude -p --agent reviewer`): Read `.env` blocked by deny rule; Edit absent from tool list; `rm -rf`/`cat .env` refused by the model before any tool call (Bash denies not exercised); `permissionMode: plan` not applied (session reported `default`).

**Caveats**
- Pattern denies are guardrails, not a sandbox.
- Bash denies are prefix matches. They miss `git push origin main --force`, `rm -f -r`, `rm --recursive`, `sh -c ...` and full-path binaries such as `/bin/rm`.
- Read denies also cover `cat`/`head`/`tail`/`sed` in Bash, but not `grep -r`, scripts (python/node) or `< .env` redirects.
- `tools:` limits the whole session under `claude --agent <name>`. With `@`-delegation it limits only the subagent, not your main thread.
- Permission arrays merge. Overlays can add denies but cannot remove allows.

**Statusline:** shows `agent: <name>`, or `agent: default` without `--agent` (`@`-delegation still shows default). It uses jq, so jq must be installed.

**Sharing:** commit `.claude/` to share with the team. Copy the agent files to `~/.claude/agents/` for personal use.

Tested with Claude Code 2.1.252.

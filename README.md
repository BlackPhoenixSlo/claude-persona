# claude-persona

Two Claude Code personas, one `.claude/agents/<name>.md` file each. Pick a persona explicitly. Claude Code may also auto-delegate to either agent based on its description.

| Name | Model | Tools | Enforced / advisory |
|------|-------|-------|---------------------|
| reviewer | opus | `Read, Grep, Glob, Bash`, `permissionMode: plan` | Tool list enforced (whole session under --agent, the subagent only via @). The git-only Bash scope is advisory: it lives in the body text, because `tools:` does not enforce Bash command patterns. |
| implementer | sonnet | `Read, Edit, Write, Grep, Glob, Bash`, `permissionMode: acceptEdits` | Tool list enforced (whole session under --agent, the subagent only via @). The body instructions are advisory. |

`permissionMode` was observed not to apply under `claude -p --agent` on 2.1.252 (session reported `default`); it applies when the persona runs as a subagent via `@agent-reviewer`, and a parent in `bypassPermissions`, `acceptEdits` or `auto` overrides it. Only the `permissions.deny` rules in `.claude/settings.json` are enforced everywhere.

**Launch:** `claude --agent reviewer` runs the whole session as the persona. `@agent-reviewer` (or pick `reviewer (agent)` from the @ menu) delegates to it mid-session.

**Verify:** under `claude --agent reviewer`, ask Claude to `rm -rf /tmp/x` and to read `.env`. Both must be refused.
Smoke test result (2026-09-27, Claude Code 2.1.252, `claude -p --agent reviewer`): pass. `rm -rf /tmp/x` refused (/tmp/x intact), Read `.env` blocked by the deny rule, Edit absent from the session tool list (README unchanged), `cat .env` refused, no secret leaked.
The reviewer refused rm/cat before calling a tool, so those Bash denies were not exercised under the persona. `permissionMode: plan` did not apply: the session init reported `default`.

**Caveats**
- Pattern denies are guardrails, not a sandbox.
- Bash denies are prefix matches. They miss `git push origin main --force`, `rm -f -r`, `rm --recursive`, `sh -c ...` and full-path binaries such as `/bin/rm`.
- Read denies also cover `cat`/`head`/`tail`/`sed` in Bash, but not `grep -r`, scripts (python/node) or, before v2.1.257, `< .env` redirects. Tested on 2.1.252.
- `tools:` limits the whole session under `claude --agent <name>`. With `@`-delegation it limits only the subagent, not your main thread.
- Permission arrays merge. Overlays can add denies but cannot remove allows.

**Statusline:** shows `agent: <name>`, or `agent: default` without `--agent` (`@`-delegation still shows default). It uses jq, so jq must be installed.

**Sharing:** commit `.claude/` to share with the team. Copy the agent files to `~/.claude/agents/` for personal use.

Tested with Claude Code 2.1.252.

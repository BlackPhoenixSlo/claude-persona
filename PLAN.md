# claude-persona — Plan

Personas for Claude Code. A persona = one `.claude/agents/<name>.md` file bundling
instructions, tool restrictions, permission mode and model. Manual selection only.

## Decisions (settled, do not reopen)

- **No LLM auto-router.** An LLM choosing a permission set from untrusted prompt text is a
  prompt-injection path. Hooks also cannot swap the system prompt mid-session.
- **One source of truth per persona:** the agent `.md` file. `claude --agent <name>` runs a
  whole session as that persona; `@<name>` delegates mid-session. No parallel `personas/*.json`.
- **Enforcement is only settings deny rules.** Subagent `tools:` scopes the subagent, not the
  main thread. A parent in `bypassPermissions`/`acceptEdits`/`auto` overrides a subagent's
  `permissionMode`. Document this; never call personas a sandbox.
- **YAGNI.** Two personas. No hook, no installer, no plugin, no architect persona. (superseded by v2)

## Deliverables

| # | Item | Acceptance |
|---|------|------------|
| 1 | `.claude/agents/reviewer.md` | `name`, `description` (one sharp line), `model: opus`, `tools: Read, Grep, Glob, Bash` (`tools:` takes plain `Bash`, not `Bash(git diff:*)`; git-only scope is advisory in the body), `permissionMode: plan`. Body: read-only review; report findings as file:line evidence + open questions; never edit, never broaden access when blocked. |
| 2 | `.claude/agents/implementer.md` | `name`, `description`, `model: sonnet`, edit tools, `permissionMode: acceptEdits`. Body: implement; report changed files and how it was validated. |
| 3 | `.claude/settings.json` | `permissions.deny` baseline: destructive rm, `git push --force`, `.env*`, `**/secrets/**`, `~/.ssh/**`. Comment in README that pattern denies are guardrails, not a sandbox. |
| 4 | Statusline | `statusLine` in settings.json shows the active agent name (or "default"). ≤10 lines of shell. |
| 5 | `README.md` (~20 lines) | Persona table (name, model, tools, enforced/advisory). Launch: `claude --agent reviewer`, `@reviewer`. Verify snippet: ask Claude to `rm -rf /tmp/x` and read `.env`; both must be refused. Caveats: subagent `tools:` scope, permission array merge (denies add, allows can't be removed by overlay). Sharing: commit `.claude/` for team, `~/.claude/agents/` for personal. Tested Claude Code version. |
| 6 | Smoke test (manual) | Run the README verify snippet under `claude --agent reviewer`; confirm both denied and reviewer cannot Edit. Record result in README. |

## Deferred (add only on signal)

- Installer / plugin packaging — used in a 3rd repo, or a 2nd person wants it.
- Architect persona — when its *instructions* differ from implementer, not just model/effort.
- Suggest-only UserPromptSubmit hook — users report forgetting to pick a persona.
- Per-persona MCP servers — a write-capable MCP server appears the reviewer must not see.
- Automated deny test harness — a deny rule regresses or CI exists.
- Cost visibility — an opus bill surprises someone; `/cost` until then.

## Facts verified (Claude Code 2.1.252, 2026-09-27)

- `claude --agent <name>` and `--settings <file|json>` exist.
- `PermissionRequest` hooks can return `updatedPermissions` mid-session; still no system-prompt swap.
- Docs: https://code.claude.com/docs/en/sub-agents , /settings , /permissions , /hooks , /cli-reference

## v2 (2026-09-27, user decision)

User expanded scope from 2 to 6 personas (opus ones get `effort: high`; orchestrator is `medium`):
- **orchestrator** — replaces the user, drives to completion, spawns Opus agents, keeps context
  low, writes `deliverables/YYYY-MM-DD/<slug>/RUN.md` as human-visible run memory.
- **reviewer** — strict thermo-nuclear review; APPROVE / REQUEST CHANGES loop.
- **devils-advocate**, **six-hats** — read-only critics.
- **operator** — browser/computer operation.
- **implementer** — model→opus, effort high.

Supersedes: "Two personas" and "no architect persona" (orchestrator fills that role).
Still holds: no LLM router; no hooks, installer or `personas/*.json`; enforcement = deny rules only.

### Next
1. Simple test project in a fresh session via `TEST_PROJECT.md`.
2. Bigger test: regenerate the DMCA website from one of the user's private repos
   (DMCAtakedownProcess, appDMCA, takedown-form-filler, IgDMCAoutreach, DmcaTG); which one is TBD by the user.

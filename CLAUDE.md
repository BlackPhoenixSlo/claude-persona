# claude-persona

Six Claude Code personas, one `.claude/agents/<name>.md` each (orchestrator, reviewer,
implementer, devils-advocate, six-hats, operator). Deny/allow rules and statusline live in
`.claude/settings.json`. User docs: `README.md`. Design record: `PLAN.md`.

Launch: `claude --agent orchestrator --permission-mode acceptEdits "<task>"`, or `@agent-<name>` mid-session.

Rules:
- YAGNI. Build only what the ask needs.
- No hooks, installer or JSON personas unless PLAN.md changes.

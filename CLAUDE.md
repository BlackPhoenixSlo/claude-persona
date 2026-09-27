# claude-persona

Claude Code personas: one `.claude/agents/<name>.md` file each (orchestrator, reviewer,
implementer, devils-advocate, six-hats, operator). Deny baseline and statusline live in
`.claude/settings.json`. Decisions and scope: `PLAN.md`.

Launch: `claude --agent orchestrator "<task>"`, or `@agent-<name>` mid-session.

Rules:
- YAGNI. Build only what the ask needs.
- No hooks, installer or JSON personas unless PLAN.md changes.

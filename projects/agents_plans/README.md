# agents_plans

The canonical area for short plans, epics, and task tracking used by contributors (agents).

Folder layout (recommended):

- `task/` — single, well-scoped work items.
- `module_or_features/` — grouped feature plans owned by a module.
- `epic/` — cross-cutting initiatives spanning multiple modules.
- `in_progress/` — move items here when active.
- `dones/` — move items here when completed.

Plan file convention:

- One markdown file per item. Include: title, owner, status, short description, acceptance criteria, and related links.
- Keep files short and link to any data samples, drafts, or PRs.

Usage:

- Create plan files before starting work and keep them updated as status changes.
- Use these plans to coordinate handoffs across modules and to document rollbacks or recovery steps for risky changes.

# agents_plans

This directory is the canonical place for agents to plan and track their work. Structure:

- `task/` — single tasks and tickets
- `epic/` — larger epics spanning multiple modules
- `module_or_features/` — feature-level plans grouped by module
- `in_progress/` — items currently being worked on
- `dones/` — completed items

Guidelines:

- Create a markdown file per plan item with a short title, owner, status, and acceptance criteria.
- Move or copy plan files into `in_progress` when work starts and into `dones` when complete.
- Keep entries small and focused; link to PRs/issue numbers when available.

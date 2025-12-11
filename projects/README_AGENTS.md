# Agents Plan Guide

Short guide for using the `agents_plans/` directory for planning and tracking work. Keep entries concise and actionable.

Directory structure (recommended):

- `task/` — single work items with a short acceptance criteria.
- `module_or_features/` — grouped feature plans owned by a module.
- `epic/` — larger initiatives spanning multiple modules.
- `in_progress/` — move items here when actively worked on.
- `dones/` — move items here once complete.

Conventions:

- One markdown file per plan item. Include: title, owner, status, short description, acceptance criteria, and links to related items.
- Use plain language and keep each file under a single screen where possible.
- For cross-team coordination, reference related module plans and list required handoffs.

This file documents the lightweight process for agents to coordinate and hand off work in the repository.

# Agents Plan Guide (Supplement)

This supplemental file describes the `agents_plans/` workflow and templates for contributors.

Repository-level planning area: `agents_plans/`

Folders:

- `task/` — single tasks and tickets
- `epic/` — larger epics spanning multiple modules
- `module_or_features/` — feature-level plans grouped by module
- `in_progress/` — items currently being worked on
- `dones/` — completed items

Guidelines:

- Create one markdown file per plan item with title, owner, status, and acceptance criteria.
- Move plan files into `in_progress/` when work starts and into `dones/` when complete.
- Keep entries small and link to related PRs/issues. Use `module_or_features/` for grouped features and `epic/` for multi-sprint efforts.

Placeholders and examples live in `agents_plans/README.md`.

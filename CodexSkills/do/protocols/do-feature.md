# do-feature protocol (5 phases)

## Phase 1 - Intake
- Parse `/do <task description>` and restate objective, constraints, acceptance criteria.
- Create task workspace under `.codex/tasks/<task-id>/`.

## Phase 2 - Analysis
- Spawn read-only agents (`explorer`, `architect`) for repository scan and implementation blueprint.
- Merge findings and produce a minimal executable plan.

## Phase 3 - Implementation
- Spawn `developer` agent to implement strictly per blueprint.
- Keep minimal diffs; preserve backward compatibility unless explicitly requested.

## Phase 4 - Validation
- Run narrow relevant tests first, then expand as needed.
- Spawn `reviewer` agent for high-confidence defects/security/style check.

## Phase 5 - Handoff
- Persist outputs to `.codex/tasks/<task-id>/` (plan, diffs, test result, review notes).
- Report findings first, then concise summary, risks, and next steps.

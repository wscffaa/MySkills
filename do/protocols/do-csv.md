# do-csv protocol (wave execution)

## Hard Constraints
- Use `apply_patch` for `.codex/tasks/*.json` and `.codex/tasks/*.md` writes. Do not generate these files with complex shell quoting/heredoc.
- Persist progress at wave granularity: after each wave, checkpoint and wave report must already exist on disk.
- For `/do-csv` (no path), resume from `.codex/tasks/csv-checkpoint.json` and do not reset completed waves.
- If the run cannot finish, checkpoint must still be updated to a recoverable state before returning.
- When all required artifacts for current request are written, return immediately with a short summary; do not continue exploratory reads.
- If user specifies exact output filenames/content contracts, follow them exactly without renaming.
- Before returning, always run: `python ~/.codex/skills/do/scripts/csv_artifact_guard.py --task-dir .codex/tasks`.
- Terminal `done` is valid only when `csv-checkpoint.json` + `csv-wave<N>-report.md`(all completed waves) + `csv-resume-report.md` are all present.

## Required Artifacts
- `.codex/tasks/csv-checkpoint.json`
- `.codex/tasks/csv-wave<N>-report.md` for each executed wave
- `.codex/tasks/csv-resume-report.md` when `/do-csv` resumes and reaches terminal state
- `.codex/tasks/csv-done.flag` when checkpoint `status=done`

## Checkpoint Schema (required keys)
- `csv_path` (string)
- `updated_at` (string, ISO-like timestamp)
- `status` (`running` | `paused_after_wave<N>` | `done` | `failed`)
- `completed_waves` (number[])
- `completed_task_ids` (string[])
- `pending_task_ids` (string[])
- `stop_reason` (string)
- `next_resume_command` (string)

## Phase 1 - Load
- Parse `/do-csv <csv path>`; if path omitted, resume last unfinished run.
- Validate CSV columns and task IDs.

## Phase 2 - Dependency Graph
- Build DAG from `depends_on`.
- Partition tasks into executable waves.

## Phase 3 - Parallel Execution
- For each wave, execute tasks in parallel with `developer` agents.
- Block next wave until current wave is stable.
- Immediately persist checkpoint + `csv-wave<N>-report.md` after finishing each wave.

## Phase 4 - Validation
- Run per-task focused tests and aggregate status.
- Re-run failed tasks only when dependency impact is understood.

## Phase 5 - Persist and Resume
- Persist state under `.codex/tasks/` and checkpoint completed task IDs.
- Output wave-level summary, failures, and resume command.
- On terminal success, write `csv-resume-report.md` (for resume flow) and set checkpoint `status=done` with `pending_task_ids=[]`.
- Run guard script; if it reports fixed artifacts, include `guard_fixed=true` in final summary.

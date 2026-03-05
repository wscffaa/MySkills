#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def normalize_waves(value) -> list[int]:
    waves: list[int] = []
    if isinstance(value, list):
        for item in value:
            try:
                number = int(item)
            except Exception:
                continue
            if number > 0:
                waves.append(number)
    return sorted(set(waves))


def ensure_wave_report(task_dir: Path, wave: int, checkpoint: dict, fixed: list[str]) -> None:
    report = task_dir / f"csv-wave{wave}-report.md"
    if report.exists():
        return
    status = checkpoint.get("status", "unknown")
    content = (
        f"# CSV Wave {wave} Report\n\n"
        f"- csv_path: `{checkpoint.get('csv_path', '')}`\n"
        f"- wave: `{wave}`\n"
        f"- status: `{status}`\n"
        f"- generated_by: `csv_artifact_guard.py`\n"
        f"- generated_at: `{now_utc()}`\n"
    )
    write_text(report, content)
    fixed.append(report.name)


def ensure_resume_report(task_dir: Path, checkpoint: dict, fixed: list[str]) -> None:
    report = task_dir / "csv-resume-report.md"
    if report.exists():
        return
    completed_waves = normalize_waves(checkpoint.get("completed_waves"))
    completed_task_ids = checkpoint.get("completed_task_ids", [])
    content = (
        "# CSV Resume Report\n\n"
        f"- resume_from: `.codex/tasks/csv-checkpoint.json`\n"
        f"- csv_path: `{checkpoint.get('csv_path', '')}`\n"
        f"- final_completed_waves: `{','.join(map(str, completed_waves))}`\n"
        f"- final_completed_task_ids: `{','.join(map(str, completed_task_ids))}`\n"
        f"- final_status: `{checkpoint.get('status', '')}`\n"
        f"- checkpoint_updated_at: `{checkpoint.get('updated_at', '')}`\n"
        f"- generated_by: `csv_artifact_guard.py`\n"
    )
    write_text(report, content)
    fixed.append(report.name)


def ensure_done_flag(task_dir: Path, checkpoint: dict, fixed: list[str]) -> None:
    done_flag = task_dir / "csv-done.flag"
    if done_flag.exists():
        return
    content = (
        f"status=done\n"
        f"updated_at={checkpoint.get('updated_at', now_utc())}\n"
        f"generated_at={now_utc()}\n"
        f"source=csv_artifact_guard.py\n"
    )
    write_text(done_flag, content)
    fixed.append(done_flag.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", default=".codex/tasks")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    checkpoint_path = task_dir / "csv-checkpoint.json"

    if not checkpoint_path.exists():
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_checkpoint",
                    "checkpoint": str(checkpoint_path),
                },
                ensure_ascii=False,
            )
        )
        return 2

    try:
        checkpoint = read_json(checkpoint_path)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "invalid_checkpoint_json",
                    "checkpoint": str(checkpoint_path),
                    "detail": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 3

    fixed: list[str] = []
    completed_waves = normalize_waves(checkpoint.get("completed_waves"))
    status = str(checkpoint.get("status", "")).strip()

    for wave in completed_waves:
        ensure_wave_report(task_dir, wave, checkpoint, fixed)

    if status == "done":
        ensure_resume_report(task_dir, checkpoint, fixed)
        ensure_done_flag(task_dir, checkpoint, fixed)

    print(
        json.dumps(
            {
                "ok": True,
                "task_dir": str(task_dir),
                "status": status,
                "completed_waves": completed_waves,
                "guard_fixed": bool(fixed),
                "fixed_files": fixed,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SYDNEY_TZ = ZoneInfo("Australia/Sydney")


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _to_sydney_iso(value: str) -> str:
    return _parse_iso(value).astimezone(SYDNEY_TZ).isoformat(timespec="seconds")


def _to_sydney_subject_ts(value: str) -> str:
    return _parse_iso(value).astimezone(SYDNEY_TZ).strftime("%Y-%m-%dT%H:%M")


def _find_latest_raw_file(raw_dir: Path) -> Path | None:
    files = sorted(raw_dir.glob("*.sleep.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _level_minutes(entry: dict, level_name: str) -> int:
    return int(entry.get("levels", {}).get("summary", {}).get(level_name, {}).get("minutes", 0) or 0)


def make_email_entries(raw_file: Path) -> list[dict]:
    payload = json.loads(raw_file.read_text(encoding="utf-8"))
    entries = []
    sleeps = payload.get("sleep", [])

    source_file = f"sleep_raw/{raw_file.name}"

    for sleep in sleeps:
        start_time_raw = sleep.get("startTime")
        end_time_raw = sleep.get("endTime")
        if not start_time_raw or not end_time_raw:
            continue

        start_time = _to_sydney_iso(start_time_raw)
        end_time = _to_sydney_iso(end_time_raw)

        body_lines = [
            f"start_time: {start_time}",
            f"end_time: {end_time}",
            f"time_in_bed_min: {sleep.get('timeInBed')}",
            f"minutes_asleep: {sleep.get('minutesAsleep')}",
            f"minutes_awake: {sleep.get('minutesAwake')}",
            f"efficiency: {sleep.get('efficiency')}",
            f"deep_min: {_level_minutes(sleep, 'deep')}",
            f"light_min: {_level_minutes(sleep, 'light')}",
            f"rem_min: {_level_minutes(sleep, 'rem')}",
            f"wake_min: {_level_minutes(sleep, 'wake')}",
            f"source_file: {source_file}",
        ]

        entries.append(
            {
                "subject": f"[Fitbit Sleep] {_to_sydney_subject_ts(start_time_raw)}",
                "body": "\n".join(body_lines),
            }
        )

    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-file", help="Path to a sleep raw JSON file")
    parser.add_argument("--raw-dir", default="out_raw", help="Directory containing *.sleep.json")
    parser.add_argument("--out-dir", default="out_emails", help="Directory for generated email JSON files")
    args = parser.parse_args()

    raw_file = Path(args.raw_file) if args.raw_file else _find_latest_raw_file(Path(args.raw_dir))
    if raw_file is None or not raw_file.exists():
        print("No raw sleep file found; skipping email generation")
        return 0

    entries = make_email_entries(raw_file)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("*.json"):
        old.unlink()

    if not entries:
        print(f"No sleep entries in {raw_file}; generated 0 email(s)")
        return 0

    for i, entry in enumerate(entries, start=1):
        out_path = out_dir / f"sleep_email_{i:02d}.json"
        out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated {len(entries)} email(s) from {raw_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
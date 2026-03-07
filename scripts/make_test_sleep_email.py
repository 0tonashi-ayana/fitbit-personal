import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def main() -> int:
    now = datetime.now(ZoneInfo("Australia/Sydney"))
    subject_ts = now.strftime("%Y-%m-%dT%H:%M")

    body = "\n".join(
        [
            f"start_time: {now.isoformat(timespec='seconds')}",
            f"end_time: {now.isoformat(timespec='seconds')}",
            "time_in_bed_min: 0",
            "minutes_asleep: 0",
            "minutes_awake: 0",
            "efficiency: 0",
            "deep_min: 0",
            "light_min: 0",
            "rem_min: 0",
            "wake_min: 0",
            "source_file: sleep_raw/test.sleep.json",
        ]
    )

    out_dir = Path("out_emails")
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("*.json"):
        old.unlink()

    payload = {
        "subject": f"[Fitbit Sleep] {subject_ts}",
        "body": body,
    }

    out_path = out_dir / "sleep_email_test.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated test email payload: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
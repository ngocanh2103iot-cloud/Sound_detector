import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import time


SCORE_RE = re.compile(
    r"^\[(?P<label>[A-Z]+)\]\s+score=(?P<score>[-+]?\d+(?:\.\d+)?)"
    r"\s+\|\s+feat=(?P<feat_ms>\d+)ms\s+infer=(?P<infer_ms>\d+)ms"
    r"(?P<tail>.*)$"
)
ALERT_RE = re.compile(r"ALERT\s+\((?P<count>\d+)\s+consecutive\)")


def parse_score_line(line):
    match = SCORE_RE.match(line.strip())
    if not match:
        return None

    tail = match.group("tail")
    alert_match = ALERT_RE.search(tail)

    return {
        "device_label": match.group("label"),
        "score": float(match.group("score")),
        "feat_ms": int(match.group("feat_ms")),
        "infer_ms": int(match.group("infer_ms")),
        "alert_count": int(alert_match.group("count")) if alert_match else 0,
        "raw_line": line.strip(),
    }


def default_output_path():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("logs") / f"score_log_{stamp}.csv"


def load_serial():
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        print("Missing dependency: pyserial", file=sys.stderr)
        print("Install it with: pip install pyserial", file=sys.stderr)
        raise SystemExit(1)

    return serial, list_ports


def list_available_ports(list_ports):
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found.", file=sys.stderr)
        return

    print("Available serial ports:", file=sys.stderr)
    for port in ports:
        print(f"  {port.device} - {port.description}", file=sys.stderr)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read ESP32 serial output, print score lines, and save them to CSV."
    )
    parser.add_argument("-p", "--port", help="Serial port, for example COM5.")
    parser.add_argument("-b", "--baud", type=int, default=921600, help="Serial baud rate.")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=default_output_path(),
        help="CSV output path.",
    )
    parser.add_argument(
        "--case",
        default="",
        help="Manual label for the test case, for example normal_room or knock_sound.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0,
        help="Seconds to record. Use 0 to run until Ctrl+C.",
    )
    return parser


def main():
    args = build_parser().parse_args()
    serial, list_ports = load_serial()

    if not args.port:
        list_available_ports(list_ports)
        print("\nPass a port with --port, for example: python Scripts/log_scores.py --port COM5")
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "host_time",
        "elapsed_s",
        "case",
        "device_label",
        "score",
        "feat_ms",
        "infer_ms",
        "alert_count",
        "raw_line",
    ]

    start = time.monotonic()
    print(f"Logging scores from {args.port} at {args.baud} baud")
    print(f"CSV: {args.out}")

    with serial.Serial(args.port, args.baud, timeout=1) as ser, args.out.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        while True:
            if args.duration > 0 and time.monotonic() - start >= args.duration:
                break

            raw = ser.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="replace").strip()
            parsed = parse_score_line(line)
            if parsed is None:
                continue

            elapsed = time.monotonic() - start
            row = {
                "host_time": datetime.now(timezone.utc).isoformat(),
                "elapsed_s": f"{elapsed:.3f}",
                "case": args.case,
                **parsed,
            }
            writer.writerow(row)
            csv_file.flush()

            alert = f" alert={parsed['alert_count']}" if parsed["alert_count"] else ""
            print(
                f"{row['elapsed_s']}s {args.case} "
                f"{parsed['device_label']} score={parsed['score']:.4f}{alert}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

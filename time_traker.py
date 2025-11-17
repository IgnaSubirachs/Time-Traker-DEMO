import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

LOG_FILE = Path("time_log.csv")


def load_log() -> pd.DataFrame:
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)
    else:
        return pd.DataFrame(columns=["date", "time", "type", "comment"])


def save_log(df: pd.DataFrame) -> None:
    df.to_csv(LOG_FILE, index=False)


def add_entry(entry_type: str, comment: str = "") -> None:
    now = datetime.now()
    df = load_log()
    new_row = {
        "date": now.date().isoformat(),
        "time": now.time().strftime("%H:%M:%S"),
        "type": entry_type.upper(),
        "comment": comment,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_log(df)
    print(f"Registered {entry_type.upper()} at {new_row['date']} {new_row['time']}")


def export_month(year: int, month: int, output_name: str | None = None) -> str:
    df = load_log()
    if df.empty:
        raise SystemExit("No records yet.")

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    filtered = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]

    if filtered.empty:
        raise SystemExit("No records for this month.")

    if output_name is None:
        output_name = f"timesheet_{year:04d}-{month:02d}.xlsx"

    filtered = filtered.sort_values(by=["date", "time"])

    filtered.to_excel(output_name, index=False)
    print(f"Exported {len(filtered)} records to {output_name}")
    return output_name


def main():
    parser = argparse.ArgumentParser(description="Simple time tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_in = subparsers.add_parser("in", help="Register check-in")
    p_in.add_argument("-c", "--comment", default="", help="Optional comment")

    p_out = subparsers.add_parser("out", help="Register check-out")
    p_out.add_argument("-c", "--comment", default="", help="Optional comment")

    p_export = subparsers.add_parser("export", help="Export a month to Excel")
    p_export.add_argument("year", type=int, help="Year, e.g. 2025")
    p_export.add_argument("month", type=int, help="Month 1-12")
    p_export.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output Excel filename (default: timesheet_YYYY-MM.xlsx)",
    )

    args = parser.parse_args()

    if args.command == "in":
        add_entry("IN", args.comment)
    elif args.command == "out":
        add_entry("OUT", args.comment)
    elif args.command == "export":
        export_month(args.year, args.month, args.output)


if __name__ == "__main__":
    main()
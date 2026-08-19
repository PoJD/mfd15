#!/usr/bin/env python3
"""Validator for CANchecked MFD15 TRI files.

A TRI file has no build, so this is the only automatic check it can get. An
error in it otherwise only shows up on the display in the car -- typically as
the file not loading at all, or as a sensor named "0" appearing.

What is checked:
  - the info; header
  - 26 columns on every sensor row, including the trailing semicolon
  - sensor names no longer than 15 characters
  - a valid CAN ID (hex, or FFF for internal sensors)
  - Format, Length and sensor type within their allowed values
  - for S-AQY.TRI additionally the exact order of the sensors and the
    verbatim text of the two Gen2 internal rows

Usage:
    python tools/validate_tri.py tri/S-AQY.TRI
    python tools/validate_tri.py tri/*.TRI tri/reference/*.TRI
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COLUMNS = 26

COL_CANID = 1
COL_FORMAT = 2
COL_START = 3
COL_LENGTH = 4
COL_MASK = 7
COL_NAME = 9
COL_TYPE = 25

MAX_NAME = 15
VALID_FORMAT = {"0", "1", "2", "4"}
VALID_TYPE = {"0", "1", "2", "3", "4"}

# Official vendor files fill unused slots with a placeholder name. It repeats
# legitimately and must not be reported as a duplicate.
PLACEHOLDER_NAMES = {"empty", "-", ""}

# Sensor order in the production file. A TRI file is addressed by position, so
# reordering rows changes which sensor sits where in the display configuration.
# Rows 17 onwards were appended rather than inserted, deliberately: the first
# sixteen keep the positions the display was already configured against.
AQY_ORDER = [
    "RPM", "Speed", "CLT", "FuelNow", "FuelAvg", "FuelTank", "Range",
    "Torque", "Power", "OilTemp", "TankL", "AccelG", "FuelCntRaw",
    "VddConv", "DisplayVolt", "DisplayTemp",
    "Flow", "TripFuel", "TripDist",
    "CanRxErr", "CanTxErr", "ComStat",
    "CanOK", "Silent", "Unhealthy", "DataLive", "PersistOK", "UnhealthyNow",
    "ResetCause", "TxRefused", "Uptime",
]

# Verified against the official Gen2 files. They write numbers in a shorter
# form than the other rows -- do not reformat.
GEN2_INTERNAL = {
    "DisplayVolt": "0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;",
    "DisplayTemp": "0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;",
}


def check(path: Path) -> list[str]:
    problems: list[str] = []
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    if not lines:
        return [f"{path}: empty file"]

    if not lines[0].startswith("info;"):
        problems.append(f"{path}:1: missing info; header")

    names: list[str] = []

    for n, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue

        if not line.endswith(";"):
            problems.append(f"{path}:{n}: row does not end with a semicolon, the display skips it")
            continue

        cols = line[:-1].split(";")
        if len(cols) != COLUMNS:
            problems.append(f"{path}:{n}: {len(cols)} columns instead of {COLUMNS}")
            continue

        name = cols[COL_NAME]
        names.append(name)

        if name == "0":
            problems.append(f"{path}:{n}: sensor named '0' -- delete the first info; row")
        elif len(name) > MAX_NAME:
            problems.append(
                f"{path}:{n}: name '{name}' is {len(name)} characters, the maximum is {MAX_NAME}")

        can_id = cols[COL_CANID]
        if can_id.upper() != "FFF":
            try:
                int(can_id, 16)
            except ValueError:
                problems.append(f"{path}:{n}: '{can_id}' is not a valid CAN ID")

        if cols[COL_FORMAT] not in VALID_FORMAT:
            problems.append(
                f"{path}:{n}: Format '{cols[COL_FORMAT]}' outside {sorted(VALID_FORMAT)}")

        if cols[COL_TYPE] not in VALID_TYPE:
            problems.append(
                f"{path}:{n}: sensor type '{cols[COL_TYPE]}' outside {sorted(VALID_TYPE)}")

        # For internal sensors column 5 is damping, not length, so it is only
        # checked on sensors that read the bus.
        if can_id.upper() != "FFF" and cols[COL_LENGTH] not in {"1", "2", "4"}:
            problems.append(f"{path}:{n}: Length '{cols[COL_LENGTH]}' should be 1, 2 or 4")

        mask = cols[COL_MASK]
        if mask:
            try:
                int(mask, 16)
            except ValueError:
                problems.append(f"{path}:{n}: mask '{mask}' is not hex")

    real = [x for x in names if x not in PLACEHOLDER_NAMES]
    dupes = {x for x in real if real.count(x) > 1}
    if dupes:
        problems.append(f"{path}: duplicate sensor names: {sorted(dupes)}")

    if path.name.upper() == "S-AQY.TRI":
        if names != AQY_ORDER:
            problems.append(
                f"{path}: sensor order does not match the expected one.\n"
                f"    expected: {AQY_ORDER}\n"
                f"    found:    {names}")
        for sensor, expected in GEN2_INTERNAL.items():
            if expected not in lines:
                problems.append(
                    f"{path}: internal sensor row {sensor} is not verbatim.\n"
                    f"    expected: {expected}")

    return problems


def expand(patterns: list[str]) -> list[Path]:
    """Expand glob patterns ourselves.

    On Linux the shell has already done this, but PowerShell passes wildcards
    through to native commands untouched, so tri/reference/*.TRI would arrive
    here verbatim.
    """
    out: list[Path] = []
    for pattern in patterns:
        path = Path(pattern)
        if path.exists() or not any(ch in pattern for ch in "*?["):
            out.append(path)
            continue
        root = path.parent if path.parent != Path("") else Path(".")
        matches = sorted(root.glob(path.name))
        out.extend(matches if matches else [path])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check TRI files.")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args(argv)

    all_problems: list[str] = []
    for path in expand(args.files):
        if not path.is_file():
            all_problems.append(f"{path}: file does not exist")
            continue
        problems = check(path)
        rows = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[1:]
        sensors = len([l for l in rows if l.strip()])
        status = "PROBLEMS" if problems else "ok"
        print(f"{path}  {sensors} sensors  {status}")
        all_problems.extend(problems)

    if all_problems:
        print()
        for p in all_problems:
            print(f"  {p}")
        print(f"\nfound {len(all_problems)} problems")
        return 1

    print("\nall files are fine")
    return 0


if __name__ == "__main__":
    sys.exit(main())

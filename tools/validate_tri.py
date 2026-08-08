#!/usr/bin/env python3
"""Validator TRI souboru pro CANchecked MFD15.

TRI nema build, takze tohle je jedina automaticka kontrola, kterou muze mit.
Chyba v nem se jinak projevi az na displeji v aute -- typicky tak, ze se
soubor vubec nenacte, nebo se objevi senzor jmenem "0".

Kontroluje se:
  - hlavicka info;
  - 26 sloupcu na kazdem radku senzoru, vcetne koncoveho strednika
  - delka nazvu do 15 znaku
  - platny CAN ID (hex nebo FFF)
  - Format, Length a typ senzoru v povolenych hodnotach
  - u S-AQY.TRI navic presne poradi 16 senzoru a doslovne zneni
    dvou internich radku Gen2

Pouziti:
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

# Oficialni vendor soubory maji nevyuzite pozice vyplnene zastupnym jmenem.
# Opakuje se legitimne a duplicitu na nich hlasit nechceme.
PLACEHOLDER_NAMES = {"empty", "-", ""}

# Poradi senzoru v produkcnim souboru. TRI se adresuje poradim, takze
# prehazeni radku zmeni, ktery senzor je na ktere pozici v konfiguraci.
AQY_ORDER = [
    "RPM", "Speed", "CLT", "FuelNow", "FuelAvg", "FuelTank", "Range",
    "Torque", "Power", "OilTemp", "TankL", "AccelG", "FuelCntRaw",
    "VddConv", "DisplayVolt", "DisplayTemp",
]

# Overeno proti oficialnim Gen2 souborum. Zapisuji cisla kratsim zpusobem
# nez ostatni radky -- nepreformatovat.
GEN2_INTERNAL = {
    "DisplayVolt": "0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;",
    "DisplayTemp": "0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;",
}


def check(path: Path) -> list[str]:
    problems: list[str] = []
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    if not lines:
        return [f"{path}: prazdny soubor"]

    if not lines[0].startswith("info;"):
        problems.append(f"{path}:1: chybi hlavicka info;")

    names: list[str] = []

    for n, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue

        if not line.endswith(";"):
            problems.append(f"{path}:{n}: radek nekonci strednikem, displej ho preskoci")
            continue

        cols = line[:-1].split(";")
        if len(cols) != COLUMNS:
            problems.append(f"{path}:{n}: {len(cols)} sloupcu misto {COLUMNS}")
            continue

        name = cols[COL_NAME]
        names.append(name)

        if name == "0":
            problems.append(f"{path}:{n}: senzor jmenem '0' -- smaz prvni radek info;")
        elif len(name) > MAX_NAME:
            problems.append(f"{path}:{n}: nazev '{name}' ma {len(name)} znaku, max je {MAX_NAME}")

        can_id = cols[COL_CANID]
        if can_id.upper() != "FFF":
            try:
                int(can_id, 16)
            except ValueError:
                problems.append(f"{path}:{n}: '{can_id}' neni platne CAN ID")

        if cols[COL_FORMAT] not in VALID_FORMAT:
            problems.append(f"{path}:{n}: Format '{cols[COL_FORMAT]}' mimo {sorted(VALID_FORMAT)}")

        if cols[COL_TYPE] not in VALID_TYPE:
            problems.append(f"{path}:{n}: typ senzoru '{cols[COL_TYPE]}' mimo {sorted(VALID_TYPE)}")

        # U internich senzoru je sloupec 5 tlumeni, ne delka, takze se
        # kontroluje jen u tech, ktere ctou sbernici.
        if can_id.upper() != "FFF" and cols[COL_LENGTH] not in {"1", "2", "4"}:
            problems.append(f"{path}:{n}: Length '{cols[COL_LENGTH]}' ma byt 1, 2 nebo 4")

        mask = cols[COL_MASK]
        if mask:
            try:
                int(mask, 16)
            except ValueError:
                problems.append(f"{path}:{n}: maska '{mask}' neni hex")

    real = [x for x in names if x not in PLACEHOLDER_NAMES]
    dupes = {x for x in real if real.count(x) > 1}
    if dupes:
        problems.append(f"{path}: duplicitni nazvy senzoru: {sorted(dupes)}")

    if path.name.upper() == "S-AQY.TRI":
        if names != AQY_ORDER:
            problems.append(
                f"{path}: poradi senzoru neodpovida ocekavanemu.\n"
                f"    ocekavano: {AQY_ORDER}\n"
                f"    nalezeno:  {names}")
        for sensor, expected in GEN2_INTERNAL.items():
            if expected not in lines:
                problems.append(
                    f"{path}: radek interniho senzoru {sensor} neni doslovny.\n"
                    f"    ocekavano: {expected}")

    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Zkontroluje TRI soubory.")
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args(argv)

    all_problems: list[str] = []
    for path in args.files:
        if not path.is_file():
            all_problems.append(f"{path}: soubor neexistuje")
            continue
        problems = check(path)
        sensors = len([l for l in path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[1:] if l.strip()])
        status = "CHYBY" if problems else "ok"
        print(f"{path}  {sensors} senzoru  {status}")
        all_problems.extend(problems)

    if all_problems:
        print()
        for p in all_problems:
            print(f"  {p}")
        print(f"\nnalezeno {len(all_problems)} problemu")
        return 1

    print("\nvsechny soubory v poradku")
    return 0


if __name__ == "__main__":
    sys.exit(main())

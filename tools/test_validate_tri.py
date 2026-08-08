#!/usr/bin/env python3
"""Tests for the TRI validator.

Besides checking the production file, these confirm the validator actually
catches things -- a validator that always says "ok" is worse than none.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_tri import AQY_ORDER, GEN2_INTERNAL, check, expand

REPO = Path(__file__).resolve().parent.parent
TRI = REPO / "tri"

HEADER = "info;1.0;0;0;0;0;0;0;0;0;0;0;-notes-;"
GOOD = "0000;0280;1;2;2;1;0;0000;0;RPM;0.25000000;0.00000000;0;0.00000000;0.00000000;0.00000000;1.00000000;0;-1.00;6500.00;255;0.00;0;0;0;0;"


class TestRealFiles(unittest.TestCase):
    def test_production_file_is_clean(self):
        self.assertEqual(check(TRI / "S-AQY.TRI"), [])

    def test_reference_files_are_clean(self):
        for path in (TRI / "reference").glob("*.TRI"):
            self.assertEqual(check(path), [], path.name)

    def test_production_file_has_16_sensors_in_order(self):
        lines = (TRI / "S-AQY.TRI").read_text(encoding="utf-8-sig").splitlines()
        names = [l[:-1].split(";")[9] for l in lines[1:] if l.strip()]
        self.assertEqual(names, AQY_ORDER)
        self.assertEqual(len(names), 16)

    def test_internal_gen2_lines_are_verbatim(self):
        text = (TRI / "S-AQY.TRI").read_text(encoding="utf-8-sig")
        for sensor, line in GEN2_INTERNAL.items():
            self.assertIn(line, text, sensor)

    def test_converter_channels_are_big_endian(self):
        """Our own frames 0x600/0x601 use Format 0, the car's frames Format 1."""
        lines = (TRI / "S-AQY.TRI").read_text(encoding="utf-8-sig").splitlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            cols = line[:-1].split(";")
            can_id, fmt, name = cols[1].upper(), cols[2], cols[9]
            if can_id in ("0600", "0601", "0602"):
                self.assertEqual(fmt, "0", f"{name} should be big endian")
            elif can_id in ("0280", "01A0", "0480"):
                self.assertEqual(fmt, "1", f"{name} should be little endian")


class TestGlobExpansion(unittest.TestCase):
    """PowerShell passes wildcards through untouched, so we expand them."""

    def test_expands_a_pattern(self):
        found = expand([str(TRI / "reference" / "*.TRI")])
        self.assertEqual(len(found), 2)
        self.assertTrue(all(p.suffix.upper() == ".TRI" for p in found))

    def test_plain_path_is_left_alone(self):
        found = expand([str(TRI / "S-AQY.TRI")])
        self.assertEqual(found, [TRI / "S-AQY.TRI"])

    def test_unmatched_pattern_is_reported_not_dropped(self):
        """A pattern matching nothing must still reach the "does not exist"
        message rather than silently validating zero files."""
        found = expand([str(TRI / "nope-*.TRI")])
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0].exists())


class TestValidatorCatchesProblems(unittest.TestCase):
    def check_text(self, text: str, name: str = "test.TRI"):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / name
            path.write_text(text, encoding="utf-8")
            return check(path)

    def one(self, text, needle, name="test.TRI"):
        problems = self.check_text(text, name)
        self.assertTrue(any(needle in p for p in problems),
                        f"expected '{needle}', got {problems}")

    def test_accepts_a_minimal_valid_file(self):
        self.assertEqual(self.check_text(f"{HEADER}\n{GOOD}\n"), [])

    def test_missing_header(self):
        self.one(f"{GOOD}\n", "missing info; header")

    def test_missing_trailing_semicolon(self):
        self.one(f"{HEADER}\n{GOOD[:-1]}\n", "does not end with a semicolon")

    def test_wrong_column_count(self):
        self.one(f"{HEADER}\n{GOOD[:-1]};extra;\n", "columns instead of 26")

    def test_name_too_long(self):
        bad = GOOD.replace(";RPM;", ";ThisNameIsWayTooLong;")
        self.one(f"{HEADER}\n{bad}\n", "the maximum is 15")

    def test_sensor_named_zero(self):
        bad = GOOD.replace(";RPM;", ";0;")
        self.one(f"{HEADER}\n{bad}\n", "delete the first info; row")

    def test_bad_can_id(self):
        bad = GOOD.replace(";0280;", ";ZZZZ;")
        self.one(f"{HEADER}\n{bad}\n", "is not a valid CAN ID")

    def test_bad_format(self):
        bad = GOOD.replace(";0280;1;", ";0280;9;")
        self.one(f"{HEADER}\n{bad}\n", "Format '9'")

    def test_duplicate_names(self):
        self.one(f"{HEADER}\n{GOOD}\n{GOOD}\n", "duplicate sensor names")

    def test_placeholder_names_are_not_duplicates(self):
        empty = GOOD.replace(";RPM;", ";empty;")
        self.assertEqual(self.check_text(f"{HEADER}\n{empty}\n{empty}\n"), [])

    def test_aqy_order_is_enforced_only_for_the_production_file(self):
        text = HEADER + "\n" + GOOD + "\n"
        self.assertEqual(self.check_text(text, "S-OTHER.TRI"), [])
        self.one(text, "sensor order", name="S-AQY.TRI")

    def test_bom_is_tolerated(self):
        self.assertEqual(self.check_text(f"﻿{HEADER}\n{GOOD}\n"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

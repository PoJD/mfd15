# The TRI format

A sensor configuration file for the CANchecked MFD15. Plain text, one line per
sensor, 26 columns separated by semicolons. Every line ends with a semicolon.

The first line is the `info;1.0;...` header.

---

## Columns

| # | Column | Meaning |
|---|---|---|
| 1 | Header | protocol; `0000` = no protocol |
| 2 | CanID | hex without a prefix; `FFF` = internal display sensor |
| 3 | Format | 0 = big endian, 1 = little endian, 2 = VEMS, 4 = IEEE float |
| 4 | Start byte | offset within the frame; channel number for internal sensors |
| 5 | Length | 1 / 2 / 4 bytes; for AIN sensors this is damping 0–249 instead |
| 6 | unsigned | 1 = unsigned |
| 7 | shift Bit | right shift applied **after** the mask — see below |
| 8 | CAN mask | hex, e.g. `007F`; `0000` = no mask |
| 9 | decimal places | how many digits after the decimal point to show |
| 10 | name | 15 characters maximum |
| 11 | initCalc | multiplier, applied to the raw value |
| 12 | initOffset | added after multiplying |
| 13 | Mappertype | 0 = linear |
| 14–17 | MapperInfo1–4 | points of the conversion curve |
| 18 | AIN active | 1 = the sensor reads an analogue input |
| 19 | Min | lower display limit |
| 20 | Max | upper display limit |
| 21 | RefSensor | index of a reference sensor; 255 = none |
| 22 | RefValue | reference value |
| 23 | — | unused |
| 24 | Pop | pop-up warning when the limits are exceeded |
| 25 | Blink | blink when the limits are exceeded |
| 26 | sensor type | 0 none, 1 pressure, 2 temperature, 3 speed, 4 air/fuel ratio |

Resulting value: `((raw & mask) >> shift) × initCalc + initOffset`

**The mask comes first and the shift second, which is the opposite of the
obvious reading.** Both official reference files agree on it and one of them
settles it outright: `S-LINKG4X.TRI` carries

```
0;38;1;7;1;1;4;F0;1;CruiseStatus;...
```

— a **one-byte** field with shift 4 and mask `F0`. Under `(raw >> 4) & 0xF0`
that is bits 8–11 of a single byte, so it would read zero always; under
`(raw & 0xF0) >> 4` it is the high nibble, which is what a four-state status
field wants. `ALS Status` (shift 5, mask `E0`), `OtherLimit` (shift 3, mask
`78`) and every single-bit row in `S-MAXX720.TRI` — `ErrorCount` shift 6 mask
`0040`, `LossSync` shift 7 mask `0080` — line up the same way and only the same
way.

So a single bit *n* is written **`shift = n`, `mask = 1 << n`**, not
`mask = 1`. The flag rows in `S-AQY.TRI` are built that way.

---

## Gen2 internal sensors

A CanID of `FFF` means the value does not come from the bus but from the
display itself. The channel number goes in column 4 (Start byte):

| Channel | What it is |
|---|---|
| 0–3 | AN1–AN4, analogue inputs |
| 4 | DisplayVolt — the display's supply voltage |
| 7 | DisplayTemp — the display's temperature |
| 10 | GearCalc |
| 11 | FlexFuel |

These two rows are copied verbatim. They are verified against the official Gen2
files and write their numbers in a shorter form than the other rows — do not
reformat them:

```
0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;
0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;
```

**DisplayVolt is also how battery voltage reaches the display.** Voltage is not
broadcast on the powertrain CAN (verified systematically, see `sensors.md`),
but the MFD15 is powered from the car through connector B, so its own supply
voltage is exactly what we want.

The 0–1023 → 0–56 V scaling comes from the official Gen2 files. If it does not
match, calibrate with two points — the procedure is in `sensors.md`.

---

## Reference files

`tri/reference/` holds two official files as examples:

- `S-LINKG4X.TRI` — Link G4X
- `S-MAXX720.TRI` — MaxxECU

They are mainly useful for confirming how internal sensors are written and what
values go in the columns that are documented nowhere.

---

## Known problems

**A sensor named "0" appears, or the file does not load at all.** Delete the
first `info;1.0;...` line and upload again. Some versions of oDSS cannot read it.

**A name longer than 15 characters** is silently truncated.

**A missing trailing semicolon** makes the display skip that line.

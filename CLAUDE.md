# mfd15 — CANchecked MFD15 Gen2 display and its TRI file

Display configuration for a VW New Beetle with the AQY engine. There is no
build here, only the data file `tri/S-AQY.TRI`, which is uploaded to the
display through oDSS.

A separate repo because the TRI file changes at a different rate than the
firmware, and because it is the one part of the project somebody else with a
Beetle and an MFD15 might want — it is usable even without the converter (six
channels then read zero).

---

## Current state — read this first

**`tri/S-AQY.TRI` is final and verified on the real display.** It was uploaded
through oDSS on 8 August 2026 and checked in the car.

- All nine channels that read the car's bus directly show correct values.
- The seven channels fed by the converter read 0, exactly as expected while
  no converter exists. That is the correct result, not a fault.
- The file loaded without the "sensor named 0" problem, so the `info;` header
  row did not need deleting on this oDSS version.

Offline validation also passes: 16 sensors in the right order, both Gen2
internal rows verbatim, `tools/validate_tri.py` clean on this file and on both
reference files, 20 tests green.

### There is no outstanding work in this repo

The TRI file is done. Do not change it speculatively.

The one thing that will require a change is the converter going live: when
`canfuel` starts transmitting 0x600–0x602, the layout in
`canfuel/docs/frames.md` and this file have to move together. That is the only
coupling between the two repos, and it runs in both directions — a change here
without a matching change there breaks the display silently, with plausible but
wrong numbers rather than an error.

At that point the useful check is comparing FuelNow against FuelCntRaw on the
display: FuelCntRaw is the raw ECU counter with no conversion, so if it rises
while FuelNow shows nonsense, the fault is in the converter's arithmetic rather
than in its input.

---

## Language

**Everything in this repository is written in English** — documentation,
scripts, comments, commit messages and file names. Conversation with the
maintainer may be in Czech; nothing written to disk ever is.

Sensor names inside the TRI file are the exception: they are fixed identifiers
the display renders, not prose, and must not be renamed.

---

## The TRI format

26 columns separated by semicolons, one line per sensor. Every line must end
with a semicolon.

| # | Column | Note |
|---|---|---|
| 1 | Header | 0000 = no protocol |
| 2 | CanID | hex without a prefix; `FFF` = internal sensor |
| 3 | Format | 0 = big endian, 1 = little, 2 = VEMS, 4 = IEEE float |
| 4 | Start byte | channel number for internal sensors |
| 5 | Length | 1/2/4; for AIN this is damping 0–249 |
| 6 | unsigned | |
| 7 | shift Bit | |
| 8 | CAN mask | hex, e.g. `007F` |
| 9 | decimal places | |
| 10 | name | 15 characters max |
| 11 | initCalc | multiplier |
| 12 | initOffset | |
| 13 | Mappertype | |
| 14–17 | MapperInfo1–4 | |
| 18 | AIN active | |
| 19 | Min | |
| 20 | Max | |
| 21 | RefSensor | 255 = none |
| 22 | RefValue | |
| 23 | — | unused |
| 24 | Pop | |
| 25 | Blink | |
| 26 | sensor type | 0 none, 1 pressure, 2 temperature, 3 speed, 4 air/fuel ratio |

### Gen2 internal sensors

Channels in column 4: 0–3 = AN1–4, 4 = DisplayVolt, 7 = DisplayTemp,
10 = GearCalc, 11 = FlexFuel.

Copy these two rows **verbatim**. They are verified against the official files
and use a shorter number format than the other rows:

```
0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;
0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;
```

---

## S-AQY.TRI — 16 sensors, do not reorder the rows

```
RPM, Speed, CLT, FuelNow, FuelAvg, FuelTank, Range, Torque, Power,
OilTemp, TankL, AccelG, FuelCntRaw, VddConv, DisplayVolt, DisplayTemp
```

Six channels (FuelNow, FuelAvg, FuelTank, Range, Torque, Power) plus VddConv
read zero until the converter exists. That is correct, not a fault.

**Big endian for our own frames.** Channels from the converter (0x600, 0x601)
use Format 0; channels from the car (0x280, 0x1A0, 0x480) use Format 1. The car
sends little endian, we send big endian — deliberately, so the two cannot be
confused.

---

## Validation

```
python -m unittest discover -s tools -p "test_*.py"
python tools/validate_tri.py tri/S-AQY.TRI
```

`tools/validate_tri.py` checks column counts, name lengths, CAN IDs and, for
S-AQY.TRI, the exact sensor order and the verbatim internal rows. It is the
only automatic check a file with no build can have.

---

## When the file does not load

If the TRI file does not load, or a sensor named "0" appears, delete the first
`info;1.0;...` line and upload it again. It is a known quirk of some oDSS versions.

---

## Checking after upload

The main evidence that the file loaded correctly is **DisplayVolt showing a
realistic ~12–14 V**. Beyond that, RPM, Speed, CLT, OilTemp, TankL, AccelG and
FuelCntRaw should all be live.

`FuelCntRaw` is the raw counter from the ECU with no conversion. It is the one
channel that reveals the converter miscalculating — when FuelNow shows
nonsense, a glance at whether this one is rising says immediately whether the
problem is in the input or in the computation.

---

## Two inaccuracies in `docs/sensors.md`

The file is otherwise valid and detailed, but two claims in it do not match
what the data showed (verified in the `canfuel` repo, `docs/can-decoding.md`).
Both are flagged inline in `sensors.md` as corrections:

1. **"bit 15 of the counter is constantly 1"** — it is not. It is zero from
   ignition on until the first wrap, then permanently one. This does not affect
   the arithmetic, since the 0x7FFF mask drops it.
2. **"the counter wraps at 32767"** — it wraps at 32768, so the modulus is 32768.

The original measurement text is kept; the corrections sit alongside it.

---

## Related repositories

- `canfuel` — the firmware that fills frames 0x600–0x602
- `kicad` — the converter board

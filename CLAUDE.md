# mfd15 — CANchecked MFD15 Gen2 display and its TRI file

Display configuration for a VW PQ34 car with the AQY engine. There is no
build here, only the data file `tri/S-AQY.TRI`, which is uploaded to the
display through oDSS.

**oDSS is not a program anybody installs, and assuming otherwise wastes real
time.** It is CANchecked's *online display setup software*, served by the
display itself over a Wi-Fi hotspot and opened in a browser — the manual is
explicit: "the oDSS starts web-based without installation via the browser of
your device" (`docs/manual-mfd15-gen2.pdf` §4). The hotspot is **off by
default**, which is the part that sends people looking for a USB port. Network
`MFD15`, password `12345678`, address `http://192.168.4.1`, and two QR codes on
the display do both steps. There is also a desktop tool of a similar name in
circulation; it is not this, and it is not needed for anything here.

A separate repo because the TRI file changes at a different rate than the
firmware, and because it is the one part of the project somebody else with a
Beetle and an MFD15 might want — it is usable even without the converter (six
channels then read zero).

---

## What this repository holds

**`tri/S-AQY.TRI` is final and verified on a real display**, uploaded through
oDSS and checked in the vehicle with the converter fitted and transmitting.

- All nine channels that read the car's bus directly show correct values.
- The ten channels fed from 0x600, 0x601 and 0x602 show correct values against
  the converter.
- The twelve channels fed from 0x603 read 0 unless the converter's `DBG_EN`
  jumper (JP1) is fitted, because that frame is not transmitted without it.
  Zero there is a missing jumper, not a fault.
- The file loaded without the "sensor named 0" problem, so the `info;` header
  row did not need deleting on this oDSS version.
- DisplayVolt reads ~12.5 V with the ignition on and ~14 V with the engine
  running, on the stock Gen2 scaling. That settles it — no calibration needed.

Offline validation also passes: 31 sensors in the right order, both Gen2
internal rows verbatim, `tools/validate_tri.py` clean on this file and on both
reference files, all tests green.

### There is no outstanding work in this repo

The TRI file is done. Do not change it speculatively — but it is no longer
frozen against the converter: every value `canfuel` transmits now has a row
here, and a new field in `canfuel/docs/frames.md` needs one adding in the same
breath.

**The project's plan lives in `canfuel/docs/install.md`** and step 2 — the one
this repository owns — is done. Nothing here tracks "what next"; that document
does, for all three repositories.

The one standing obligation is the coupling to the converter: the layout in
`canfuel/docs/frames.md` and the rows here have to move together. It runs in
both directions — a change on either side without a matching change on the
other breaks the display silently, with plausible but wrong numbers rather than
an error. All four frames, 0x600 to 0x603, now have rows here, so the coupling
covers every field the converter transmits.

The useful check on the display is comparing FuelNow against FuelCntRaw:
FuelCntRaw is the raw ECU counter with no conversion, so if it rises while
FuelNow shows nonsense, the fault is in the converter's arithmetic rather than
in its input.

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

## S-AQY.TRI — 31 sensors, do not reorder the rows

```
RPM, Speed, CLT, FuelNow, FuelAvg, FuelTank, Range, Torque, Power,
OilTemp, TankL, AccelG, FuelCntRaw, VddConv, DisplayVolt, DisplayTemp,
Flow, TripFuel, TripDist,
CanRxErr, CanTxErr, ComStat,
CanOK, Silent, Unhealthy, DataLive, PersistOK, UnhealthyNow,
ResetCause, TxRefused, Uptime
```

**APPEND, NEVER INSERT.** A TRI file is addressed by position and the display
is already configured against the first sixteen. Everything after
`DisplayTemp` was appended for exactly that reason, and the two Gen2 internal
rows being in the middle of the file rather than at the end is a consequence of
it, not an error — `S-LINKG4X.TRI` has its internal rows in the middle too.
`test_the_first_sixteen_positions_never_move` holds this.

**The last twelve rows read frame 0x603, which the converter transmits only
while its `DBG_EN` jumper is fitted.** They read zero without it, and that is
the design rather than a fault. The point of having them is that "is the CAN
side healthy" can be answered on the display instead of with a laptop and a
USBtin.

**Single bits are `shift = n`, `mask = 1 << n`** — the mask is applied first
and the shift second. That is not the obvious reading and it is settled by the
official reference files; the evidence is in `docs/tri-format.md`.

**Big endian for our own frames.** Channels from the converter (0x600–0x603)
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

## ⚠ Operating oDSS puts errors on the CAN bus

**Observed in the vehicle, with the converter fitted:** uploading a TRI file,
and changing the display's configuration, each produced a burst of CAN errors.
The converter's `LED_CAN` blinked for a few seconds, its latched `UNHEALTHY`
flag came on, and it stayed on until the next power-up. The error counters
walked back to zero on their own straight afterwards and nothing was lost.

Three things follow, in order of how much they are worth:

- **Do not diagnose the converter for it.** `UNHEALTHY` set with the error
  counters at zero, after somebody has been in oDSS, is very probably this.
  Power-cycle before reading that flag as a verdict on anything.
- **It cannot happen while driving.** oDSS needs the display's Wi-Fi hotspot
  and the hotspot is off by default, so this belongs to setup and to nothing
  else.
- **What the display actually does is NOT established** — whether it transmits
  malformed frames, resets its own CAN controller, or floods the bus while it
  reads or writes its configuration. Only the correlation is known, taken by
  watching the converter's 0x603 diagnostic frame while operating oDSS. **If
  this is ever raised with CANchecked, raise the correlation and not a
  mechanism.** A capture with `canfuel/tools/usbtin_capture.py` across an
  upload would say what actually goes onto the wire, and nobody has run one.

`canfuel/docs/frames.md` carries the same note where somebody debugging the
converter will meet it.

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

Two siblings sit next to this one, with separate toolchains and separate GitHub
remotes under `PoJD/`. The directory above them is deliberately not a git repo,
so always run git inside one of the three.

- `canfuel` — the firmware that fills frames 0x600–0x603
- `kicad` — the converter board

**`canfuel/docs/refuted.md` collects the refuted hypotheses of all three
repositories.** The two inaccuracies above are entries B7 and B8 there, and the
byte once mislabelled as tank level is B2. It is one file rather than three so
that a plausible idea somebody is about to have again can be found from any of
them. When something here is settled *against*, add it there and keep the
detail here.

Installed on the development machine: git, gcc, make, Python 3.11. This repo
needs none of them beyond Python.

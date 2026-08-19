# mfd15

Configuration for a CANchecked MFD15 Gen2 display in a VW PQ34 car with the
AQY engine (2.0 l / 85 kW, PQ34).

This repository has no build. It holds the data file `tri/S-AQY.TRI` and the
documentation for the format.

## Status

**Final.** `tri/S-AQY.TRI` has been uploaded to the display and verified in the
vehicle, with the converter fitted and transmitting. Every channel that reads
the vehicle's bus shows correct values, and so do the converter's.

The twelve channels fed from frame 0x603 read 0 unless the converter's `DBG_EN`
jumper (JP1) is fitted — that frame is not transmitted at all without it. Zero
there is a missing jumper, not a fault.

**The whole build path, across all three repositories, is
[`canfuel/docs/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/install.md).**
The step this repository owns is step 2, and it is done.

## What the file does

31 sensors. Nine of them read the car's powertrain CAN directly and work on
their own, with no converter present at all:

RPM, Speed, CLT, OilTemp, TankL, AccelG, FuelCntRaw, DisplayVolt, DisplayTemp

Ten are filled by the `canfuel` converter from frames 0x600, 0x601 and 0x602,
which it transmits whenever it is powered:

FuelNow, FuelAvg, FuelTank, Range, Torque, Power, Flow, VddConv, TripFuel,
TripDist

The remaining twelve decode the converter's diagnostic frame 0x603, which is
**only transmitted while JP1 is fitted**:

CanRxErr, CanTxErr, ComStat, CanOK, Silent, Unhealthy, DataLive, PersistOK,
UnhealthyNow, ResetCause, TxRefused, Uptime

`canfuel/docs/frames.md` is the authority on every layout above, and the flag
and reset-cause bits are tabulated there.

**Rows are appended, never inserted.** A TRI file is addressed by position and
the display is already configured against the first sixteen; putting a new
sensor in the middle silently repoints every gauge after it.

## Prerequisites

**There is nothing to install.** That is worth stating plainly, because the
obvious assumption is wrong: oDSS is not a desktop application. It is
CANchecked's *online display setup software*, served by the display itself and
opened in a browser — "the oDSS starts web-based without installation via the
browser of your device" (`docs/manual-mfd15-gen2.pdf` §4).

| For | What | Notes |
|---|---|---|
| uploading to the display | **any Wi-Fi device with a browser** | phone or laptop; the display serves oDSS over its own hotspot |
| validating the file first | **Python 3.11+** | no third-party packages |

```
python tools/validate_tri.py tri/S-AQY.TRI     # needs no display at all
```

**Validation needs nothing but Python**, which is the point of it: the file is
addressed by row position and a display will load a malformed one without
complaining, so it is worth checking before it ever reaches the hardware.

The display itself is a **CANchecked MFD15 Gen2**. The file is written for that
generation — `docs/tri-format.md` explains what is generation-specific.

## Uploading the file

oDSS runs **in the display**, not on your computer. This duplicates part of
`docs/manual-mfd15-gen2.pdf` on purpose — the manual describes the display,
this describes getting *this* file into it.

**0. Download `tri/S-AQY.TRI` onto the device you will upload from** — a phone
or a laptop, anything with Wi-Fi and a browser. Do it **now, before anything
else**: from step 3 that device is joined to the display's hotspot and has no
internet, so a file you have not already downloaded is a file you cannot get.

**1. Power the display up.** Ignition on with the display plugged in — in
practice that means **plug B**, which carries its 12 V. **The CAN pair is not
needed for this.** Uploading a TRI file is a conversation between the browser
and the display; it does not touch the car's bus at all. CAN only matters from
step 6, when you want to see real values. So this can be done on a bench with
any 12 V supply, off the car entirely.

**2. Press both buttons on the display until a QR code appears.** This is what
turns the Wi-Fi hotspot on — it is **off by default**, and it is the step that
sends people looking for a USB port. It is needed **every time**: the hotspot
does not stay on by itself.

**3. Scan the QR code with the device from step 0.** It joins the display's
hotspot. After the first time this step is optional — the phone will rejoin the
network on its own — but **step 2 is not**, because there is no network to
rejoin until the display is asked for one.

**4. Open `http://192.168.4.1`** in the browser. That is oDSS.

**5. Upload to device**, and pick the TRI file from step 0. Then activate it.

**6. Check it against the car.** The CAN icon must be **green** — that is the
display saying it is seeing the bus — and the sensor list must match the
thirty-one under *What the file does* above, showing live values for the nine
that read the car directly. The ten fed by the converter read 0 until `canfuel`
transmits, and the twelve fed by 0x603 read 0 unless the converter's `DBG_EN`
jumper is fitted. Both are correct rather than a fault.

**Confirming the upload alone, with no car:** `DisplayVolt` must show a
realistic ~12–14 V. It is an internal sensor of the display, so it is live
without a bus, which makes it the one channel that separates *the file loaded*
from *the wiring works*.

If the file does not load, or a sensor named "0" appears, delete the first
`info;1.0;...` line and upload it again.

Anything beyond this — the buttons, the pages, the rest of oDSS — is in
[`docs/manual-mfd15-gen2.pdf`](docs/manual-mfd15-gen2.pdf), §4 for the
connection and §6 for oDSS itself.

## Uploading puts errors on the CAN bus, briefly

**Observed in the vehicle with the converter fitted:** uploading a TRI file, and
changing the display's configuration, each produced a burst of CAN errors. The
converter's `LED_CAN` blinked for a few seconds and its latched `UNHEALTHY`
flag came on and stayed on until the next power-up, while its error counters
walked back to zero on their own straight afterwards. Nothing was lost.

**Nothing needs doing about it**, and there are two reasons to know it anyway:

- **Do not diagnose the converter for it.** That flag set with the error
  counters at zero, after somebody has been in oDSS, is very probably this.
  Power-cycle before reading it as a verdict on anything.
- **It cannot happen while driving.** oDSS needs the display's Wi-Fi hotspot
  and the hotspot is off by default, so this belongs to setup and nowhere else.

What the display actually does is **not established** — see `CLAUDE.md` before
repeating this anywhere it might be taken as a mechanism.

---

## After changing pages, upload the file again

**The display sometimes loses its sensor definitions when a page's contents are
changed**, taking the other pages' configuration with it. RPM vanishing is the
tell. Uploading `tri/S-AQY.TRI` again fixes it every time, so upload it again
as a matter of course after any page change rather than waiting to notice.

It is the display's own fault, not this file's: the same thing happens with
CANchecked's own TRI files and with no converter connected. `CLAUDE.md` has
what was observed and what is still unexplained.

---

## Validation

```
python tools/validate_tri.py tri/S-AQY.TRI
python -m unittest discover -s tools -p "test_*.py"
```

## Layout

```
tri/
  S-AQY.TRI              production file, 31 sensors
  reference/             official Gen2 files used as examples
docs/
  sensors.md             description of every sensor and where it comes from
  tri-format.md          26 columns, meaning of each
  manual-mfd15-gen2.pdf  original manual (in German/English as shipped)
tools/
  validate_tri.py        format checker used by CI
```

## Do not reorder the rows

A TRI file is addressed by position. Reordering rows changes which sensor sits
where in the display configuration.

## Related repositories

This repository is useful **on its own** — nine of the sixteen sensors read the
car's bus directly, so a Beetle with an MFD15 and no converter still gets rpm,
speed, coolant, oil, tank level, acceleration and the raw fuel counter. The
other seven need the converter, which is the other two repositories. Clone them
side by side if you want the whole thing.

**Building the whole thing?** [`canfuel/docs/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/install.md)
is the path from three clones to a working device, in the order it has to
happen. Uploading the TRI file — the part that lives here — is step 2 of seven.

| Repository | What it holds | Go there for |
|---|---|---|
| **`mfd15`** (this one) | the display configuration | `tri/S-AQY.TRI`, `docs/sensors.md` — what every gauge reads and where it comes from |
| [`canfuel`](https://github.com/PoJD/canfuel) | the converter firmware | how the seven converter channels are computed; `docs/frames.md` is the layout this repository consumes |
| [`kicad`](https://github.com/PoJD/kicad) | the converter board | `canfuel/docs/harness.md` — **how to make the loom and wire it into the car**, including the plug C pins this display supplies the converter from |

**The coupling that can bite** is the layout of frames 0x600 and 0x601:
`canfuel/docs/frames.md` defines it and `tri/S-AQY.TRI` consumes it. If one
changes without the other, nothing errors — the display just shows plausible
wrong numbers, which is worse. `canfuel/test/test_txframes.c` pins every offset
against this file and quotes the relevant TRI lines in its header.

## Licence

[Apache License 2.0](LICENSE), covering `tri/S-AQY.TRI`, the documentation and
the tools. Use it, change it, adapt it to your own car — the only obligations
are to keep the copyright and licence notices and to say what you changed.

**`NOTICE` lists what is not ours.** The MFD15 manual and the two official
example TRI files under `tri/reference/` are CANchecked's and are here for
reference only; the licence above does not cover them and does not claim to.

Questions, corrections and pull requests are welcome as issues on any of the
three repositories, or by email to Lubos Housa <luboshousa@gmail.com>.

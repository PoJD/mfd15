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

The last ten rows, frame 0x604, have been uploaded with the rest and read in
the car against the converter: `IdleHealth` left 255 after half a minute of
idle and settled on a plausible value, `StartCrank` shows the start, and the
other rows read as expected. The first thirty-one rows kept their positions.

**The eighteen rows after them, frames 0x605 to 0x607** (22/11/2026): each
cylinder's share of a standing idle, and a summary of this drive's and the
previous drive's warm idles. **Uploaded and read in the car on 22/11/2026**,
two drives with long warm stops: the four cylinders, `CylWeak` and `CylNamed`
plausible block by block, this drive's rows filling from the warm idle, and the
previous drive's reading 255 until a record was stored, then showing the drive
before after the next power-up. `CylBlocks`, the two `WeakCyl` rows and
`PrvStored` were on no page and are not seen yet. The first forty-one rows keep
their positions.

**The whole build path, across all three repositories, is
[`canfuel/docs/firmware/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/firmware/install.md).**
The step this repository owns is step 2, and it is done.

## What the file does

59 sensors. Nine of them read the car's powertrain CAN directly and work on
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

The last ten decode the converter's engine-health frame 0x604, which is
transmitted **whenever the converter is powered** — it is for a closed
dashboard. Its "not known" is **255 in every field**, never zero, and the whole
frame reads 255 while the bus is quiet:

IdleHealth, Misfires, IdleSec, MisfAvg, StartCrank, StartDip,
StartClt, IdleNow, StartSeen, HealthLive

The last seven decode the cylinder frame 0x605, transmitted like 0x604
whenever the converter is powered: each cylinder's deviation from the four's
mean at a standing idle, in per cent of one stroke, the weakest cylinder, how
many 19-second blocks of idle the values come from, and whether the naming
of the cylinders was clear. 255 is "not known" here too; on the display it
reads +63.5 on the four cylinder rows:

Cyl1, Cyl2, Cyl3, Cyl4, CylWeak, CylBlocks, CylNamed

The last eleven decode 0x606 and 0x607: a summary of the warm standing idle
(oil at 85 °C and above) of this drive, and of the previous one as the
converter's EEPROM kept it — minutes of warm idle, the mean IdleHealth, the
misfire estimate per minute, the weakest cylinder's mean deviation and which
cylinder it was; PrvStored says a previous drive was found at all:

DrvIdleMin, DrvHealth, DrvMisf, DrvWeak, DrvWeakCyl,
PrvIdleMin, PrvHealth, PrvMisf, PrvWeak, PrvWeakCyl, PrvStored

`canfuel/docs/firmware/frames.md` is the authority on every layout above, and the flag
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

## *(optional)* The start image

The display shows a picture at power-up, and **any picture will do** — this
step is optional and nothing else depends on it. `logo/logo.bmp` is just this
car's: a photograph of it, cropped to a square around the car and scaled
down, with no other change. Make your own the same way.

**The display accepts a start image only on these terms**
(`docs/manual-mfd15-gen2.pdf` §6.3 and §9.5):

- **24-bit BMP.** Not PNG or JPEG, and renaming a PNG does not make it a BMP.
  Any image editor that can "save as BMP, 24 bit" will do; the manual
  suggests MS Paint.
- **At most 128 × 128 pixels.** §9.5 says 128 × 128, so make it exactly that.
- **The file is named exactly `logo.bmp`.**

**What the manual does not say, and the display does** (firmware 4.112):

- **The picture is drawn square, edge to edge.** The housing is round, but
  the OLED panel inside it is square (seen by the owner with the unit
  dismantled), so nothing is clipped to a circle and the corners show.
- **The boot screen writes the firmware version and serial number over the
  bottom rows.** Keep anything that matters out of the bottom tenth or so.
- **A plain photograph looks better than a cut-out.** The first version here
  was the car cut out onto black; it displayed correctly but looked
  artificial, and the uncut photograph replaced it.

**Uploading it:** download `logo.bmp` onto the phone first, then steps 1 to 4
of *Uploading the file* above, then **Upload File** in oDSS. The progress bar
reports success, and the picture appears at the **next** power-up, not at
once. **If it comes up with colours it does not contain, upload it again**:
that happened here once, and the same file uploaded a second time was
correct, so it was the transfer and not the file. **On older firmware a
picture upload overwrote the TRI file** — CANchecked's changelog lists the
fix in v4.100e — so on anything older, upload the TRI file again afterwards;
RPM missing is the tell.

Verified on this display, firmware 4.112, 22/11/2026: both versions showed
at the next power-up and nothing else changed.

---

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

## A gauge's maximum and its highlighting are set on the page, not here

Each gauge on a page has two checkboxes in oDSS's page settings (the
manual, §6.1.4 *Pages*, names the first; the second observed by the
owner, 22/11/2026, display firmware 4.112):

- **Max** shows the maximum reached this drive beneath the value.
- **Highlight warnings** colours the value against the warning limits —
  the TRI file's Min and Max (columns 19 and 20; the manual, §8.1, calls
  them the lower and upper warning value).

With both cleared the gauge shows the current value and nothing else.
**Clear both for values that are a state, not a measurement** —
`CylNamed`, `CylWeak`, the `Prv…` rows, `Uptime`, the flags — where a
maximum means nothing and a value sitting on its Max is normal:
`CylNamed` at 1 and `CylWeak` at 4 showed yellow until they were cleared.
Keep them for real measurements (oil temperature, `FuelTank`, `Range`).
**This is the display's setting, not the file's**: the limits in the TRI
file need no change for it.

---

## Validation

```
python tools/validate_tri.py tri/S-AQY.TRI
python -m unittest discover -s tools -p "test_*.py"
```

## Layout

```
tri/
  S-AQY.TRI              production file, 59 sensors
  reference/             official Gen2 files used as examples
logo/
  logo.bmp               start image: the car photo, 128 x 128, 24-bit BMP
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

**Building the whole thing?** [`canfuel/docs/firmware/install.md`](https://github.com/PoJD/canfuel/blob/main/docs/firmware/install.md)
is the path from three clones to a working device, in the order it has to
happen. Uploading the TRI file — the part that lives here — is step 2 of seven.

| Repository | What it holds | Go there for |
|---|---|---|
| **`mfd15`** (this one) | the display configuration | `tri/S-AQY.TRI`, `docs/sensors.md` — what every gauge reads and where it comes from |
| [`canfuel`](https://github.com/PoJD/canfuel) | the converter firmware | how the seven converter channels are computed; `docs/firmware/frames.md` is the layout this repository consumes |
| [`kicad`](https://github.com/PoJD/kicad) | the converter board | `canfuel/docs/harness.md` — **how to make the loom and wire it into the car**, including the plug C pins this display supplies the converter from |

**The coupling that can bite** is the layout of frames 0x600 and 0x601:
`canfuel/docs/firmware/frames.md` defines it and `tri/S-AQY.TRI` consumes it. If one
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

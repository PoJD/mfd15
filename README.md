# mfd15

Configuration for a CANchecked MFD15 Gen2 display in a VW New Beetle with the
AQY engine (2.0 l / 85 kW, PQ34).

This repository has no build. It holds the data file `tri/S-AQY.TRI` and the
documentation for the format.

## Status

**Final.** `tri/S-AQY.TRI` was uploaded to the display and verified in the car
on 8 August 2026. Every channel that reads the car's bus shows correct values;
the channels fed by the `canfuel` converter read 0, as expected while that
converter does not exist yet.

## What the file does

16 sensors. Nine of them read the car's powertrain CAN directly and work on
their own:

RPM, Speed, CLT, OilTemp, TankL, AccelG, FuelCntRaw, DisplayVolt, DisplayTemp

The other seven are filled by the `canfuel` converter from frames 0x600 and
0x601. Until the converter exists they read zero — and that is correct:

FuelNow, FuelAvg, FuelTank, Range, Torque, Power, VddConv

## Uploading the file

1. Connect the display to a computer and start oDSS.
2. Open `tri/S-AQY.TRI` and upload it to the display.
3. Activate it.

**Confirming it worked:** DisplayVolt must show a realistic ~12–14 V. That is
the key piece of evidence — it is an internal display sensor, so it is live
even without a car on the bus.

If the file does not load, or a sensor named "0" appears, delete the first
`info;1.0;...` line and upload it again.

## Validation

```
python tools/validate_tri.py tri/S-AQY.TRI
python -m unittest discover -s tools -p "test_*.py"
```

## Layout

```
tri/
  S-AQY.TRI              production file, 16 sensors
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

- `canfuel` — converter firmware, fills frames 0x600–0x602
- `kicad` — the converter board

## Licence

[Apache License 2.0](LICENSE), covering `tri/S-AQY.TRI`, the documentation and
the tools. Use it, change it, adapt it to your own car — the only obligations
are to keep the copyright and licence notices and to say what you changed.

**`NOTICE` lists what is not ours.** The MFD15 manual and the two official
example TRI files under `tri/reference/` are CANchecked's and are here for
reference only; the licence above does not cover them and does not claim to.

Questions, corrections and pull requests are welcome as issues on any of the
three repositories.

# Sensors in S-AQY.TRI — full description

Beetle AQY (2.0 l / 85 kW), powertrain CAN at 500 kbps, CANchecked MFD15 Gen2
display. State as of 2 August 2026.

---

## Overview

| # | Name in TRI | What it is | Source | Works immediately? |
|---|---|---|---|---|
| 1 | RPM | engine speed | 0x280 b2-3 | ✅ yes |
| 2 | Speed | vehicle speed | 0x1A0 b2-3 | ✅ yes |
| 3 | CLT | coolant temperature | 0x288 b1 | ✅ yes |
| 4 | FuelNow | instantaneous consumption l/100 km | 0x600 b0-1 | ❌ needs converter |
| 5 | FuelAvg | average consumption l/100 km | 0x600 b2-3 | ❌ needs converter |
| 6 | FuelTank | fuel in tank, damped | 0x600 b4-5 | ❌ needs converter |
| 7 | Range | range estimate in km | 0x600 b6-7 | ❌ needs converter |
| 8 | Torque | torque in Nm | 0x601 b2-3 | ❌ needs converter |
| 9 | Power | instantaneous power in kW | 0x601 b0-1 | ❌ needs converter |
| 10 | OilTemp | oil temperature | 0x420 b3 | ✅ yes |
| 11 | TankL | fuel in tank, raw from the car | 0x320 b2 | ✅ yes |
| 12 | AccelG | longitudinal/lateral acceleration | 0x5A0 b0 | ✅ yes |
| 13 | FuelCntRaw | raw fuel counter from the ECU | 0x480 b2-3 | ✅ yes |
| 14 | DisplayVolt | display supply voltage (= car's 12 V) | MFD internal sensor | ✅ yes, after calibration |
| 15 | VddConv | the 5 V rail as the converter sees it | 0x601 b6-7 | ❌ needs converter |

Yes, six values will read zero until the converter exists — those are #4–#9.
The seventh, #15, is a new addition described below.

> **Verified on hardware, 8 August 2026.** The file was uploaded through oDSS
> and checked in the car. Every channel marked ✅ shows correct values, and the
> converter-fed channels read 0 as expected. The table above is no longer a
> prediction.

---

## 1. RPM — engine speed

- **Source:** 0x280 (Motor 1) bytes 2–3, little endian
- **Formula:** `raw × 0.25` = rpm
- **Verified:** idle raw 0x0C76 = 3190 → 797 rpm; log 05 raw 11741 → 2935 rpm
- **Range:** 0–8000; exactly 0 with the engine off
- **Note:** the ECU sends 0x280 every ~10.5 ms, making it the fastest reliable
  "clock" on the bus. The converter firmware uses it for timing even though it
  has its own timer.

## 2. Speed — vehicle speed

- **Source:** 0x1A0 (Motor 2) bytes 2–3, little endian
- **Formula:** `raw × 0.005` = km/h
- **Validity:** the value is valid **only when byte 1 == 0x40**. After the
  ignition is switched on the message runs an init ramp for ~0.4 s (raw falls
  464 → 0) during which byte 1 is 0x43. That has to be discarded, otherwise the
  converter would briefly see 2.3 km/h out of nowhere.

  > **Correction from phase 0.** Byte 1 is a bit field, not a single value.
  > 0x48 and 0x50 are equally valid states and 0x48 is in fact the majority in
  > `07_accel.txt`. The correct rule is `(b1 & 0x40) && !(b1 & 0x03)`. See
  > `canfuel/docs/can-decoding.md`.

- **Factor 0.005, not 0.01:** determined from the fact that the whole test
  drive was in first gear — max raw 3879 → 19.4 km/h at ~2560 rpm, which fits
  first gear. With a factor of 0.01 it would come out as 38.8 km/h, which first
  gear cannot do.
- **Cross-check:** 0x4A0 carries four wheel speeds as 16-bit LE, where
  `(raw >> 1) × 0.01` km/h and bit 0 is the direction of rotation. It agrees
  with 0x1A0 to within ±1 km/h.

## 3. CLT — coolant temperature

- **Source:** 0x288 (Motor 3) byte 1
- **Formula:** `raw × 0.75 − 48` = °C
- **Fault value:** 0xFF
- **Verified:** a monotonic warm-up curve across all five logs,
  68 → 90 → 94.5 → 99 → 100.5 °C. Also confirmed by an external source
  (the OSM wiki on VW-CAN).
- **Note:** the same temperature also appears in 0x420 byte 4, but damped by
  the instrument cluster (slower rise so the needle does not jump). 0x288 is
  the better choice for the display.

## 4. FuelNow — instantaneous consumption

- **Source:** converter frame 0x600 bytes 0–1, big endian
- **Formula:** `raw × 0.1` = l/100 km
- **How the converter computes it:** from the counter in 0x480 (µl) and the
  speed from 0x1A0. `l/100km = (µl/s ÷ metres/s) × 0.1`
- **Corner case:** below 5 km/h it sends 999 → the display shows 99.9. That is
  intentional, the same as OEM trip computers do.

  > **Correction from phase 0.** The threshold ended up at 4.0 km/h and below
  > it the channel switches to l/h rather than clamping. See
  > `canfuel/docs/frames.md`.

- **Smoothing:** a ~1 s rolling average, otherwise the number dances unreadably.

## 5. FuelAvg — average consumption

- **Source:** 0x600 bytes 2–3, big endian
- **Formula:** `raw × 0.1` = l/100 km
- **How the converter computes it:** as the ratio of two accumulators — total
  microlitres consumed ÷ total metres driven. **Not** as an average of
  instantaneous values; that would be mathematically wrong (standing at a red
  light with infinite instantaneous consumption would destroy the average).
- **Persistence:** the accumulators are written to EEPROM once every 60 s,
  circular buffer, 64 slots.
- **Reset:** will hook into the cluster's trip reset if it turns out trip
  kilometres are broadcast on the bus. Otherwise a Can Switch from the MFD15.

  > **Superseded in phase 0.** The reset is now tied to refuelling, which needs
  > neither a sniff nor a licence. See `canfuel/docs/refuel-reset.md`.

## 6. FuelTank — fuel in tank (damped)

- **Source:** 0x600 bytes 4–5, big endian
- **Formula:** `raw × 0.1` = litres
- **Difference from TankL (#11):** the same quantity, but run through a 60 s
  time constant in the converter. The float in the tank sloshes on every corner
  and every brake application; the raw value would jump around on the display.
  This is the channel that actually makes sense to show.

## 7. Range — range estimate

- **Source:** 0x600 bytes 6–7, big endian
- **Formula:** `raw × 1` = km
- **How the converter computes it:** `litres remaining ÷ (rolling consumption
  over the last 30 km) × 100`. The rolling average runs over 1 km segments,
  so 30 slots — which is why the estimate behaves like a modern car's: after
  flooring it on the motorway it falls gradually rather than jumping.
- **Corner case:** until at least 5 km have been driven since startup, a
  conservative default of 9 l/100 km is used so the estimate is not nonsense
  on a cold start.

## 8. Torque

- **Source:** 0x601 bytes 2–3, big endian
- **Formula:** `raw × 0.1` = Nm
- **Why it goes through the converter and not straight from 0x280 b7:** the ECU
  sends **indicated** torque, i.e. what the combustion produces, not what
  reaches the wheels. Drag torque (friction, pumps, alternator) has to be
  subtracted, and it is not constant — it rises with engine speed. The
  converter models it linearly against rpm, calibrated at two points: idle and
  3000 rpm in neutral. Both are already in the logs.
- **Source scaling:** bytes 1, 4 and 7 of 0x280 carry three torque variants
  (driver request / indicated / internal) at ~0.39 % per bit. The AQY maximum
  is 172 Nm → 0.67 Nm per bit.
- **Realism:** the ME7 does not measure torque, it models it from air mass per
  stroke with corrections for ignition advance and lambda. The 100 % figure is
  a calibration constant in the ECU that an ordinary chip tune does not change.
  The numbers are therefore indicative, not dyno-grade.

## 9. Power

- **Source:** 0x601 bytes 0–1, big endian
- **Formula:** `raw × 0.1` = kW
- **Why through the converter:** `power = torque × rpm ÷ 9550`. The MFD15
  cannot compute it — per the manual, the math channels (MathChannel1-8) exist
  only on the MFD28/32 Gen2. The MFD15 does not have them, so the converter has
  to compute it and send the finished value.

## 10. OilTemp — oil temperature

- **Source:** 0x420 (Kombi 1) byte 3
- **Formula:** `raw × 0.75 − 48` = °C
- **Fault value:** 0xFF (in log 01, ignition on without the engine running, it
  is exactly 0xFF; in log 05 at 3000 rpm it reads 116 → 39 °C)
- **⚠️ Unconfirmed:** the OSM VW-CAN wiki says 0x420 b3 is oil. The car is not
  expected to have an oil temperature sensor. Across the session the value rose
  21 → 39 → 61 → 66 °C, a slower rise than the coolant — which is an argument
  **for** oil. IAT (intake air) would track the engine bay temperature while
  standing and would drop when accelerating. A brisk drive settles it.

  > **Phase 0 update.** `07_accel.txt` was recorded for exactly this. The
  > temperature holds at 75.75 → 76.5 °C during the acceleration and does not
  > fall, which argues for oil — but the run was only 16 s, so it is still not
  > conclusive.

- **Bytes 1 and 2 of 0x420** are, according to the source, ambient temperature
  `(raw−100)/2`; both read 0x00 here, so there is no ambient temperature sensor.

## 11. TankL — fuel in tank (raw)

- **Source:** 0x320 byte 2, mask 0x7F
- **Formula:** `raw & 0x7F` = litres directly, no conversion
- **Bit 0x80** = reserve lamp lit
- **Current data:** exactly 0x80 in every log, i.e. **0 litres with the reserve
  lamp on**. That matches the usage pattern — running it right down to disperse
  the original petrol, then topping up 5–6 l from a jerrycan.
- **What it is for in the TRI file:** a diagnostic/reference channel. Once the
  converter exists, FuelTank (#6) is what gets watched on the display. TankL
  shows what the car actually sends before the converter smooths it — useful
  when debugging and when verifying the value really is in litres (refuel a
  known amount and compare).

## 12. AccelG — acceleration

- **Source:** 0x5A0 (Bremse 2) byte 0
- **Formula:** `(raw − 127) ÷ 100` = G
- **Yes, it is acceleration**, but note: **it is not certain whether
  longitudinal or lateral.** The source does not say. The data shows a stable
  127–128 (= 0 G) at rest, 110–153 while driving (−0.17 to +0.26 G) and 118–119
  after stopping. That offset after stopping is either the slope of the ground
  (longitudinal sensor) or a permanent bias. If it is longitudinal, parking
  across a slope settles it reliably.
- **Historical note:** this byte was previously mislabelled as tank level.
  That was wrong and has been corrected.

## 13. FuelCntRaw — raw fuel counter

- **Source:** 0x480 bytes 2–3, little endian, mask 0x7FFF
- **Yes, this is exactly what the ECU sends**, with no conversion.
- **Unit: 1 = 1 microlitre.** Not a guess — confirmed by an independent
  external source (the YBW forum, a VAG CAN reading project) and consistent
  with everything our own data shows.
- **Behaviour:** the counter only moves forwards, is **15-bit** (bit 15 must be
  masked away) and wraps at 32767. It **resets to zero** when the ignition is
  switched off — verified in log 01, where all 81 frames read exactly 0x0000.

  > **Correction from phase 0.** Two details are wrong here. Bit 15 is not
  > constant: it is zero from ignition on until the first wrap, then
  > permanently one. And the counter wraps at 32768, so the modulus is 32768,
  > not 32767. Neither affects the arithmetic, since the mask drops bit 15.
  > See `canfuel/docs/can-decoding.md`.

- **Measured flow rates:**
  - warm idle at 797 rpm → 310 µl/s = **1.12 l/h**
  - 2940 rpm unloaded (log 05) → 958 µl/s = **3.45 l/h**

  > **Phase 0 update.** The idle figure reproduces exactly, but only after
  > de-duplicating `02_idle_60s.txt`, which contains the recording twice. The
  > 2940 rpm figure measures 1005 µl/s rather than 958; the gap is in the
  > assumed frame period, not in the data.

- **Why you want it on the display:** it is the one channel that reveals the
  converter miscalculating. When FuelNow shows nonsense, a glance at whether
  this one is rising says immediately whether the problem is in the input or in
  the computation.
- **Firmware trap:** the delta is computed `(new − old) mod 32768`. After an
  engine start the counter begins at zero, so without restart detection the
  delta would jump nonsensically by tens of thousands of µl. Detection:
  `counter == 0 || rpm == 0` → reinitialise `prev`.

---

## Voltage — what was found and what to do about it

### There is no voltage on the CAN bus

Both logs were searched systematically: every byte of every ID, plus all 16-bit
combinations in both LE and BE, looking for a value that would jump by the
right ~15 % between "ignition only" (~12.2 V) and "3000 rpm" (~14.2 V) and
convert to a voltage under some sensible scaling.

**Nothing turned up.** Four bytes do have that ratio, but none of them can be it:

| Byte | ign → rev | Why it is not voltage |
|---|---|---|
| 0x050 b2, b3 | 112 → 128 | 16 unique values in steps of 16 = a rolling counter/checksum |
| 0x320 b0 | 64 → 69 | door bit mask |
| 0x5A0 b0 | 119 → 128 | acceleration (AccelG) |

That also makes sense theoretically: on the PQ34 the instrument cluster
measures battery voltage for itself and does not broadcast it on the powertrain
CAN. It is available through diagnostics (VCDS measuring blocks), not by broadcast.

**One caveat for honesty:** 0x520 appeared only 1–2 times per log, so a very
slow frame carrying voltage cannot be ruled out with total certainty. But all
its bytes are identical between logs apart from a counter, which makes it unlikely.

### Solution for 12 V: the display's internal sensor

The MFD15 is powered from the car through connector B, so **its own supply
voltage is the voltage you want.** The internal `displayVolt` sensor measures
it directly. The fact that the DSS will not connect to the display does not
matter — editing the TRI offline to add an internal sensor is enough. The only
problem is that the correct scaling for Gen2 is unknown (Gen1 used 0–1023 →
0–53 V, which is different hardware).

> **Settled, 8 August 2026. No calibration needed.** With the stock Gen2
> scaling from the official files (`0–1023 → 0–56 V`, the `DisplayVolt` row
> copied verbatim) the channel reads correctly on the real display:
>
> - ignition on, engine stopped → **~12.5 V**
> - engine running → **~14 V**
>
> That is exactly the expected battery and alternator behaviour, so the
> scaling is right and the two-point procedure below was never needed. It is
> kept only in case a future display or firmware version scales differently.

**The two-point calibration, if it is ever needed:**

1. Add a TRI row for the internal voltage sensor but with **raw scaling**:
   initCalc = 1, initOffset = 0, decimal places = 0, mapper output = input over
   a 0–4095 range. The display then shows the bare ADC number.
2. Ignition on, engine stopped. Measure the voltage with a multimeter and note
   the pair (raw₁, V₁).
3. Start the engine and hold 3000 rpm. Measure again → (raw₂, V₂).
4. Compute `a = (V₂ − V₁) / (raw₂ − raw₁)` and `b = V₁ − a × raw₁`.
5. Put initCalc = a, initOffset = b, decimal places = 1 into the TRI file.

Two points are enough because the divider is linear. Measure **at the display
connector, not at the battery** — there are a few tenths of a volt of drop in
the wiring to the dashboard, and otherwise that resistance would be baked into
the constant.

**Fallback if the internal sensor does not work:** the MFD15 Gen2 has six
analogue inputs. Use a divider from 12 V into AIN1 and column 18 (AIN active)
in the TRI file. This does not need the Can Switching licence — that one is
only for *transmitting*.

### Solution for 5 V: let the converter measure it itself

This is a good idea and costs zero components. The catch is that a PIC cannot
measure its own supply the ordinary way — the ADC measures against VDD, so it
would always see full scale on VDD.

It is worked around the other way round: **the PIC18F25K80 has a built-in fixed
voltage reference (FVR) of 1.024 V that the ADC can read as an input channel.**
So you measure the FVR against VDD and work backwards:

```
VDD = 1.024 × 1023 / ADC_result
```

Zero external components, zero pins. (Worth confirming in the datasheet when we
write the firmware — the principle is solid, but the register names for the K80
series should be verified rather than recalled.)

**Added to the frames like this:** 0x601 has bytes 6–7 free, so `VddConv` goes
there as `raw × 0.01` = V. Range 4.50–5.50 V, two decimal places on the display.

**And yes, there is CPU capacity to spare.** A PIC18F25K80 at 16 MHz manages
4 million instructions per second. The whole computation — two divisions for
consumption, one multiplication for power, a few rolling averages — is on the
order of thousands of instructions per 100 ms frame. Utilisation will be a few
percent. The only genuinely tight resource is RAM (3.6 kB) because of the 30
rolling-average slots for range, and even that fits comfortably.

---

## Still to verify

None of these block the TRI file, which is finished. They are open questions
about the signals themselves and belong to the `canfuel` work.

1. **Trip reset on the cluster** — a sniff with a reset. Superseded for the
   purpose of resetting the average, which is now tied to refuelling, but the
   question of whether trip kilometres are broadcast is still unanswered.
   `06_trip_reset.txt` was recorded for it and has not been analysed.
2. **Is 0x420 b3 oil or IAT?** — a brisk drive. IAT would drop, oil would not.
   `07_accel.txt` argues for oil (the value held at 75.75 → 76.5 °C during the
   pull-away) but the run was only 16 s, so it is not conclusive.
3. **AccelG: longitudinal or lateral?** — park across a slope.
4. **0x288 b5 and b6** — load-dependent, undecoded. Candidates are MAF,
   ignition advance and injection time. Fastest route is comparing against
   VCDS measuring blocks.
5. **Drag torque calibration** — both points are already in the logs (idle and
   3000 rpm in neutral); they just need substituting in.

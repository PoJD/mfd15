# mfd15 — displej CANchecked MFD15 Gen2 a jeho TRI soubor

Konfigurace displeje pro VW New Beetle, motor AQY. Nemá build, jen datový
soubor `tri/S-AQY.TRI`, který se do displeje nahrává přes oDSS.

Oddělené repo proto, že TRI se mění jinou frekvencí než firmware a je to
jediná část projektu, kterou by mohl chtít někdo jiný s Beetlem a MFD15 —
je použitelná i bez převodníku (šest kanálů pak ukazuje nulu).

---

## Formát TRI

26 sloupců oddělených středníkem, každý řádek jeden senzor. Řádek musí končit
středníkem.

| # | Sloupec | Poznámka |
|---|---|---|
| 1 | Header | 0000 = bez protokolu |
| 2 | CanID | hex, bez prefixu; `FFF` = interní senzor |
| 3 | Format | 0 = big endian, 1 = little, 2 = VEMS, 4 = IEEE float |
| 4 | Start byte | u interních senzorů číslo kanálu |
| 5 | Length | 1/2/4; u AIN = tlumení 0–249 |
| 6 | unsigned | |
| 7 | shift Bit | |
| 8 | CAN maska | hex, např. `007F` |
| 9 | desetinná místa | |
| 10 | název | max 15 znaků |
| 11 | initCalc | násobitel |
| 12 | initOffset | |
| 13 | Mappertype | |
| 14–17 | MapperInfo1–4 | |
| 18 | AIN active | |
| 19 | Min | |
| 20 | Max | |
| 21 | RefSensor | 255 = žádný |
| 22 | RefValue | |
| 23 | — | nepoužito |
| 24 | Pop | |
| 25 | Blink | |
| 26 | typ senzoru | 0 none, 1 tlak, 2 teplota, 3 rychlost, 4 spalovací poměr |

### Interní senzory Gen2

Kanály ve sloupci 4: 0–3 = AN1–4, 4 = DisplayVolt, 7 = DisplayTemp,
10 = GearCalc, 11 = FlexFuel.

Tyhle dva řádky **kopírovat doslova**, jsou ověřené proti oficiálním souborům
a mají jiný počet znaků než ostatní (kratší zápis čísel):

```
0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;
0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;
```

---

## S-AQY.TRI — 16 senzorů, pořadí řádků neměnit

```
RPM, Speed, CLT, FuelNow, FuelAvg, FuelTank, Range, Torque, Power,
OilTemp, TankL, AccelG, FuelCntRaw, VddConv, DisplayVolt, DisplayTemp
```

Šest kanálů (FuelNow, FuelAvg, FuelTank, Range, Torque, Power) plus VddConv
ukazuje nulu, dokud neexistuje převodník. To je správně, ne chyba.

**Big endian pro vlastní rámce.** Kanály z převodníku (0x600, 0x601) mají
Format 0, kanály z auta (0x280, 0x1A0, 0x480) mají Format 1. Auto posílá
little endian, my big endian — schválně, ať se to nedá splést.

---

## Když se soubor nenačte

Když se TRI nenačte nebo se objeví senzor jménem „0", smazat první řádek
`info;1.0;...` a nahrát znovu. Je to známá vlastnost některých verzí oDSS.

---

## Kontrola po nahrání

Hlavní důkaz, že se soubor načetl správně, je **DisplayVolt ukazující
reálných ~12–14 V**. Dál mají žít RPM, Speed, CLT, OilTemp, TankL, AccelG
a FuelCntRaw.

`FuelCntRaw` je surový čítač z ECU bez přepočtu. Je to jediný kanál, kterým
se pozná, že převodník počítá blbě — když FuelNow ukáže nesmysl, stačí se
podívat, jestli tenhle roste, a hned je jasné, jestli je problém ve vstupu,
nebo ve výpočtu.

---

## Pozor: `docs/sensors.md` má dvě nepřesnosti

Soubor je jinak platný a podrobný, ale dvě věci v něm neodpovídají tomu,
co ukázala data (ověřeno v repu `canfuel`, `docs/can-decoding.md`):

1. **„bit 15 čítače je konstantně 1"** — není. Je nula od zapnutí zapalování
   do prvního přetečení, pak trvale jedna. Na výpočet to vliv nemá, maska
   0x7FFF ho zahodí.
2. **„čítač přetéká na 32767"** — přetéká na 32768, tedy modulo je 32768.

Nepřepisuje se to, aby zůstal původní text měření; opravy jsou tady.

---

## Související repozitáře

- `canfuel` — firmware, který plní rámce 0x600–0x602
- `kicad` — deska převodníku

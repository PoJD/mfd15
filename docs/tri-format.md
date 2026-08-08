# Formát TRI

Konfigurační soubor senzorů pro CANchecked MFD15. Prostý text, jeden řádek =
jeden senzor, 26 sloupců oddělených středníkem. Řádek končí středníkem.

První řádek je hlavička `info;1.0;...`.

---

## Sloupce

| # | Sloupec | Význam |
|---|---|---|
| 1 | Header | protokol; `0000` = bez protokolu |
| 2 | CanID | hex bez prefixu; `FFF` = interní senzor displeje |
| 3 | Format | 0 = big endian, 1 = little endian, 2 = VEMS, 4 = IEEE float |
| 4 | Start byte | offset v rámci; u interních senzorů číslo kanálu |
| 5 | Length | délka 1 / 2 / 4 bajty; u AIN místo toho tlumení 0–249 |
| 6 | unsigned | 1 = bez znaménka |
| 7 | shift Bit | posun doprava před aplikací masky |
| 8 | CAN maska | hex, např. `007F`; `0000` = bez masky |
| 9 | desetinná místa | kolik číslic za desetinnou čárkou zobrazit |
| 10 | název | max 15 znaků |
| 11 | initCalc | násobitel, aplikuje se na surovou hodnotu |
| 12 | initOffset | přičte se po vynásobení |
| 13 | Mappertype | 0 = lineární |
| 14–17 | MapperInfo1–4 | body převodní křivky |
| 18 | AIN active | 1 = senzor čte analogový vstup |
| 19 | Min | dolní mez zobrazení |
| 20 | Max | horní mez zobrazení |
| 21 | RefSensor | index referenčního senzoru; 255 = žádný |
| 22 | RefValue | referenční hodnota |
| 23 | — | nepoužito |
| 24 | Pop | vyskakovací upozornění při překročení mezí |
| 25 | Blink | blikání při překročení mezí |
| 26 | typ senzoru | 0 none, 1 tlak, 2 teplota, 3 rychlost, 4 spalovací poměr |

Výsledná hodnota: `((raw >> shift) & maska) × initCalc + initOffset`

---

## Interní senzory Gen2

CanID `FFF` znamená, že hodnota nepochází ze sběrnice, ale z displeje.
Číslo kanálu je ve sloupci 4 (Start byte):

| Kanál | Co to je |
|---|---|
| 0–3 | AN1–AN4, analogové vstupy |
| 4 | DisplayVolt — napájecí napětí displeje |
| 7 | DisplayTemp — teplota displeje |
| 10 | GearCalc |
| 11 | FlexFuel |

Tyto dva řádky se kopírují doslova. Jsou ověřené proti oficiálním Gen2
souborům a zapisují čísla kratším způsobem než ostatní řádky — nepřeformátovat:

```
0;FFF;0;4;230;0;0;0;1;DisplayVolt;1;0;1;0;1023;0;56;1;10;16;255;0;0;0;0;0;
0;FFF;0;7;0;0;0;0;0;DisplayTemp;1;0;0;0;0;0;0;1;0;100;255;0;0;0;0;2;
```

**DisplayVolt je zároveň způsob, jak dostat na displej napětí baterie.**
Na hnací CAN se napětí nevysílá (systematicky ověřeno, viz `sensors.md`),
ale MFD15 je napájený z auta přes konektor B, takže jeho vlastní napájecí
napětí je přesně to, co chceme.

Škálování 0–1023 → 0–56 V je z oficiálních Gen2 souborů. Když nesedí,
kalibruje se dvěma body — postup je v `sensors.md`.

---

## Reference

V `tri/reference/` jsou dva oficiální soubory jako vzory:

- `S-LINKG4X.TRI` — Link G4X
- `S-MAXX720.TRI` — MaxxECU

Hodí se hlavně na ověření, jak se zapisují interní senzory a jaké hodnoty
jsou v sloupcích, které nikde nejsou popsané.

---

## Známé problémy

**Senzor jménem „0" nebo se soubor vůbec nenačte.** Smazat první řádek
`info;1.0;...` a nahrát znovu. Některé verze oDSS ho neumí přečíst.

**Název delší než 15 znaků** se tiše ořízne.

**Chybějící koncový středník** na řádku způsobí, že se řádek přeskočí.

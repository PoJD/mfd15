# mfd15

Konfigurace displeje CANchecked MFD15 Gen2 pro VW New Beetle s motorem AQY
(2,0 l / 85 kW, PQ34).

Repozitář nemá build. Je v něm datový soubor `tri/S-AQY.TRI` a dokumentace
k formátu.

## Co soubor umí

16 senzorů. Devět z nich čte přímo hnací CAN auta a funguje samo o sobě:

RPM, Speed, CLT, OilTemp, TankL, AccelG, FuelCntRaw, DisplayVolt, DisplayTemp

Zbylých sedm plní převodník `canfuel` z rámců 0x600 a 0x601. Dokud převodník
neexistuje, ukazují nulu — a je to tak správně:

FuelNow, FuelAvg, FuelTank, Range, Torque, Power, VddConv

## Jak se soubor nahraje

1. Připojit displej k počítači a spustit oDSS.
2. Otevřít `tri/S-AQY.TRI` a nahrát do displeje.
3. Aktivovat.

**Kontrola, že se to povedlo:** DisplayVolt musí ukazovat reálných ~12–14 V.
To je hlavní důkaz — je to interní senzor displeje, takže žije i bez auta
na sběrnici.

Když se soubor nenačte nebo se objeví senzor jménem „0", smazat první řádek
`info;1.0;...` a nahrát znovu.

## Struktura

```
tri/
  S-AQY.TRI              produkční soubor, 16 senzorů
  reference/             oficiální Gen2 soubory jako vzory
docs/
  sensors.md             popis všech senzorů a odkud pocházejí
  tri-format.md          26 sloupců, význam každého
  manual-mfd15-gen2.pdf  originální manuál
```

## Pořadí řádků neměnit

TRI se adresuje pořadím. Přeházení řádků změní, který senzor je na které
pozici v konfiguraci displeje.

## Související repozitáře

- `canfuel` — firmware převodníku, plní rámce 0x600–0x602
- `kicad` — deska převodníku

## Licence

Zatím neurčeno.

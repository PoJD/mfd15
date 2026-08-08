# Senzory v S-AQY.TRI — kompletní popis

Beetle AQY (2,0 l / 85 kW), hnací CAN 500 kbps, displej CANchecked MFD15 Gen2.
Stav k 2. 8. 2026.

---

## Přehled

| # | Název v TRI | Co to je | Zdroj | Funguje hned? |
|---|---|---|---|---|
| 1 | RPM | otáčky motoru | 0x280 b2-3 | ✅ ano |
| 2 | Speed | rychlost vozidla | 0x1A0 b2-3 | ✅ ano |
| 3 | CLT | teplota chladicí kapaliny | 0x288 b1 | ✅ ano |
| 4 | FuelNow | okamžitá spotřeba l/100 km | 0x600 b0-1 | ❌ převodník |
| 5 | FuelAvg | průměrná spotřeba l/100 km | 0x600 b2-3 | ❌ převodník |
| 6 | FuelTank | palivo v nádrži, tlumené | 0x600 b4-5 | ❌ převodník |
| 7 | Range | odhad dojezdu v km | 0x600 b6-7 | ❌ převodník |
| 8 | Torque | točivý moment Nm | 0x601 b2-3 | ❌ převodník |
| 9 | Power | okamžitý výkon kW | 0x601 b0-1 | ❌ převodník |
| 10 | OilTemp | teplota oleje | 0x420 b3 | ✅ ano |
| 11 | TankL | palivo v nádrži, surově z auta | 0x320 b2 | ✅ ano |
| 12 | AccelG | podélné/příčné zrychlení | 0x5A0 b0 | ✅ ano |
| 13 | FuelCntRaw | surový čítač spotřeby z ECU | 0x480 b2-3 | ✅ ano |
| 14 | DisplayVolt | napájecí napětí displeje (= 12V auta) | interní senzor MFD | ✅ ano, po kalibraci |
| 15 | VddConv | 5V větev, kterou vidí převodník | 0x601 b6-7 | ❌ převodník |

**Ano, 6 hodnot bude ukazovat nulu, dokud nebude převodník** — jsou to #4–#9.
Sedmá, #15, je nový návrh níže. Ty čtyři, o kterých jsem psal dřív, byly jen ty
z rámce 0x600; zapomněl jsem připočíst moment a výkon z 0x601.

---

## 1. RPM — otáčky motoru

- **Zdroj:** 0x280 (Motor 1) bajty 2–3, little endian
- **Vzorec:** `raw × 0,25` = ot/min
- **Ověřeno:** volnoběh raw 0x0C76 = 3190 → 797 ot/min; log 05 raw 11741 → 2935 ot/min
- **Rozsah:** 0–8000, při vypnutém motoru přesně 0
- **Poznámka:** ECU vysílá 0x280 každých ~10,5 ms, takže je to nejrychlejší
  spolehlivé „hodiny" na sběrnici. Firmware převodníku toho využívá pro
  časování, i když má vlastní timer.

## 2. Speed — rychlost vozidla

- **Zdroj:** 0x1A0 (Motor 2) bajty 2–3, little endian
- **Vzorec:** `raw × 0,005` = km/h
- **Platnost:** hodnota je platná **jen když bajt 1 == 0x40**. Po zapnutí
  zapalování dělá zpráva ~0,4 s inicializační rampu (raw klesá 464 → 0) a
  během ní je bajt 1 = 0x43. To se musí zahodit, jinak by převodník na
  půl sekundy viděl 2,3 km/h z ničeho.
- **Faktor 0,005, ne 0,01:** určeno z toho, že celá testovací jízda byla na
  jedničku — max raw 3879 → 19,4 km/h při ~2560 ot/min, což odpovídá prvnímu
  převodovému stupni. S faktorem 0,01 by vycházelo 38,8 km/h, což na jedničku
  nejde.
- **Křížová kontrola:** 0x4A0 nese čtyři rychlosti kol jako 16bit LE, kde
  `(raw >> 1) × 0,01` km/h a bit 0 je směr otáčení. Souhlasí s 0x1A0 na ±1 km/h.

## 3. CLT — teplota chladicí kapaliny

- **Zdroj:** 0x288 (Motor 3) bajt 1
- **Vzorec:** `raw × 0,75 − 48` = °C
- **Chybová hodnota:** 0xFF
- **Ověřeno:** napříč všemi pěti logy monotónní zahřívací křivka
  68 → 90 → 94,5 → 99 → 100,5 °C. Potvrzeno i externím zdrojem (OSM wiki VW-CAN).
- **Poznámka:** stejná teplota je i v 0x420 bajt 4, ale tlumená přístrojovkou
  (pomalejší náběh, aby ručička neskákala). Pro displej je lepší 0x288.

## 4. FuelNow — okamžitá spotřeba

- **Zdroj:** rámec převodníku 0x600 bajty 0–1, big endian
- **Vzorec:** `raw × 0,1` = l/100 km
- **Jak to počítá převodník:** z čítače v 0x480 (µl) a rychlosti z 0x1A0.
  `l/100km = (µl/s ÷ ujeté m/s) × 0,1`
- **Corner case:** při rychlosti pod 5 km/h se posílá 999 → displej ukáže
  99,9. To je záměr, stejně jako to dělají OEM palubní počítače.
- **Vyhlazení:** klouzavý průměr ~1 s, jinak by číslo tancovalo nečitelně.

## 5. FuelAvg — průměrná spotřeba

- **Zdroj:** 0x600 bajty 2–3, big endian
- **Vzorec:** `raw × 0,1` = l/100 km
- **Jak to počítá převodník:** jako podíl dvou akumulátorů — celkem spotřebované
  mikrolitry ÷ celkem ujeté metry. **Ne** jako průměr okamžitých hodnot; ten by
  byl matematicky špatně (stání na semaforu s nekonečnou okamžitou spotřebou by
  průměr zničilo).
- **Persistence:** akumulátory se ukládají do EEPROM 1× za 60 s, kruhový buffer
  64 slotů.
- **Reset:** naváže se na trip reset přístrojovky, pokud se potvrdí, že se trip
  km na sběrnici vysílají (test po návratu z Indie). Jinak Can Switch z MFD15.

## 6. FuelTank — palivo v nádrži (tlumené)

- **Zdroj:** 0x600 bajty 4–5, big endian
- **Vzorec:** `raw × 0,1` = litry
- **Rozdíl proti TankL (#11):** tohle je tatáž veličina, ale prohnaná přes
  60sekundovou časovou konstantu v převodníku. Plovák v nádrži šplouchá při
  každém zatáčení a brzdění; syrová hodnota by na displeji poskakovala.
  Tenhle kanál je ten, který má smysl skutečně zobrazovat.

## 7. Range — odhad dojezdu

- **Zdroj:** 0x600 bajty 6–7, big endian
- **Vzorec:** `raw × 1` = km
- **Jak to počítá převodník:** `zbylé litry ÷ (klouzavá spotřeba na posledních
  30 km) × 100`. Klouzavý průměr je po segmentech 1 km, tedy 30 slotů — proto
  se odhad chová jako v moderních autech: po sešlápnutí plynu na dálnici
  postupně klesá, neskočí okamžitě.
- **Corner case:** dokud není najetých aspoň 5 km od startu, použije se
  konzervativní default 9 l/100 km, aby odhad nebyl při studeném startu nesmysl.

## 8. Torque — točivý moment

- **Zdroj:** 0x601 bajty 2–3, big endian
- **Vzorec:** `raw × 0,1` = Nm
- **Proč jde přes převodník a ne přímo z 0x280 b7:** ECU posílá **indikovaný**
  moment, tedy to, co produkují spaliny, ne to, co jde na kola. Musí se odečíst
  ztrátový moment (tření, čerpadla, alternátor), který není konstantní — roste
  s otáčkami. Převodník ho modeluje lineárně podle otáček, kalibrovaný ve dvou
  bodech: volnoběh a 3000 ot/min v neutrálu. Obojí už v logách máme.
- **Škálování zdroje:** 0x280 bajty 1, 4 a 7 nesou tři varianty momentu
  (požadavek řidiče / indikovaný / vnitřní), ~0,39 % na bit. U AQY je maximum
  172 Nm → 0,67 Nm na bit.
- **Realismus:** ME7 moment neměří, modeluje ho z hmotnosti vzduchu na zdvih
  s korekcemi na předstih a lambdu. 100 % je kalibrační konstanta v ECU, kterou
  běžný čip nemění. Čísla jsou tedy indikativní, ne dynamometrická.

## 9. Power — okamžitý výkon

- **Zdroj:** 0x601 bajty 0–1, big endian
- **Vzorec:** `raw × 0,1` = kW
- **Proč přes převodník:** `výkon = moment × otáčky ÷ 9550`. MFD15 to spočítat
  neumí — math kanály (MathChannel1-8) jsou podle manuálu jen pro MFD28/32 Gen2.
  MFD15 je nemá. Takže to musí spočítat převodník a poslat hotové.

## 10. OilTemp — teplota oleje

- **Zdroj:** 0x420 (Kombi 1) bajt 3
- **Vzorec:** `raw × 0,75 − 48` = °C
- **Chybová hodnota:** 0xFF (v logu 01 se zapalováním bez motoru je tam přesně
  0xFF, v logu 05 při 3000 ot/min je 116 → 39 °C)
- **⚠️ Nepotvrzeno:** OSM wiki VW-CAN říká pro 0x420 b3 olej. Ty čekáš, že
  čidlo teploty oleje v autě nemáš. Přes session hodnota rostla 21 → 39 → 61
  → 66 °C, což je pomalejší náběh než chladicí kapalina — a to je argument
  **pro** olej. IAT (nasávaný vzduch) by při stání kopíroval teplotu motorového
  prostoru a při rozjezdu by spadl. Rozhodne svižná jízda.
- **Bajt 1 a 2 v 0x420** jsou podle zdroje venkovní teplota `(raw−100)/2`,
  u tebe obojí 0x00 → čidlo venkovní teploty nemáš.

## 11. TankL — palivo v nádrži (surově)

- **Zdroj:** 0x320 bajt 2, maska 0x7F
- **Vzorec:** `raw & 0x7F` = litry přímo, bez přepočtu
- **Bit 0x80** = rozsvícená rezerva
- **Tvoje aktuální data:** ve všech logách přesně 0x80, tedy **0 litrů + svítí
  rezerva**. Sedí to na to, co říkáš — dojíždíš na doraz, aby se rozmělnil
  původní benzin, a pak doléváš 5–6 l z kanystru.
- **K čemu to je v TRI:** jako kontrolní/diagnostický kanál. Až budeš mít
  převodník, budeš na displeji sledovat FuelTank (#6). TankL ti řekne, co
  posílá auto, než to převodník vyhladí — užitečné při ladění a při ověřování,
  jestli je hodnota opravdu v litrech (natankuj známé množství a porovnej).

## 12. AccelG — zrychlení

- **Zdroj:** 0x5A0 (Bremse 2) bajt 0
- **Vzorec:** `(raw − 127) ÷ 100` = G
- **Ano, je to akcelerace**, ale pozor: **není jisté, jestli podélná nebo
  příčná.** Zdroj to neupřesňuje. Tvoje data ukazují v klidu stabilně 127–128
  (= 0 G), za jízdy kolísání 110–153 (−0,17 až +0,26 G) a po zastavení
  118–119. Ten offset po zastavení je buď sklon pozemku (podélný senzor), nebo
  trvalá odchylka. Pokud je podélný, spolehlivě to rozhodneš tím, že
  zaparkuješ napříč na svahu.
- **Historická poznámka:** dřív jsem tenhle bajt chybně označil za stav
  nádrže. To bylo špatně, opraveno.

## 13. FuelCntRaw — surový čítač spotřeby

- **Zdroj:** 0x480 bajty 2–3, little endian, maska 0x7FFF
- **Ano, je to přesně to, co posílá ECU**, bez jakéhokoli přepočtu.
- **Jednotka: 1 = 1 mikrolitr.** Není to odhad — potvrzeno nezávislým externím
  zdrojem (fórum YBW, projekt čtení VAG CANu) a shoduje se se vším, co vyšlo
  z tvých vlastních dat.
- **Chování:** čítač jede jen dopředu, je **15bitový** (bit 15 je konstantně 1,
  musí se maskovat pryč) a přetéká na 32767. Při vypnutí zapalování se
  **resetuje na nulu** — ověřeno v logu 01, kde je celých 81 rámců přesně
  0x0000.
- **Naměřené průtoky:**
  - zahřátý volnoběh 797 ot/min → 310 µl/s = **1,12 l/h**
  - 2940 ot/min bez zátěže (log 05) → 958 µl/s = **3,45 l/h**
- **Proč to chceš mít na displeji:** je to jediný kanál, kterým poznáš, že
  převodník počítá blbě. Když FuelNow ukáže nesmysl, podíváš se, jestli
  tenhle roste — a hned víš, jestli je problém ve vstupu, nebo ve výpočtu.
- **Past pro firmware:** delta se počítá `(nový − starý) mod 32768`. Po startu
  motoru začíná čítač od nuly, takže bez detekce restartu by delta dala
  nesmyslný skok o desítky tisíc µl. Detekce: `čítač == 0 || otáčky == 0`
  → reinicializovat `prev`.

---

## Napětí — co jsem zjistil a co s tím

### Na CAN sběrnici napětí není

Projel jsem oba logy systematicky: každý bajt každého ID, plus všechny
16bitové kombinace v LE i BE, a hledal jsem hodnotu, která by mezi „jen
zapalování" (~12,2 V) a „3000 ot/min" (~14,2 V) vyskočila o těch správných
zhruba 15 % a dala se rozumným škálováním převést na napětí.

**Nic to nenašlo.** Čtyři bajty sice ten poměr mají, ale žádný z nich to
nemůže být:

| Bajt | ign → rev | Proč to není napětí |
|---|---|---|
| 0x050 b2, b3 | 112 → 128 | 16 unikátních hodnot po násobcích 16 = rolovací čítač/checksum |
| 0x320 b0 | 64 → 69 | bitová maska dveří |
| 0x5A0 b0 | 119 → 128 | zrychlení (AccelG) |

To dává smysl i teoreticky: na PQ34 měří napětí baterie přístrojovka pro sebe
a na hnací CAN ho nevysílá. Dostupné je přes diagnostiku (měřené bloky VCDS),
ne broadcastem.

**Jedna výhrada k poctivosti:** 0x520 se v každém logu objevilo jen 1–2×, takže
velmi pomalý rámec s napětím nelze vyloučit se 100% jistotou. Ale všechny jeho
bajty jsou mezi logy identické kromě čítače, takže je to nepravděpodobné.

### Řešení pro 12 V: interní senzor displeje

MFD15 je napájený z auta přes konektor B, takže **jeho vlastní napájecí napětí
je to napětí, které chceš.** Interní senzor `displayVolt` ho měří přímo. To,
že se DSS nepřipojí k displeji, nevadí — offline editace TRI na přidání
interního senzoru stačí. Problém je jen v tom, že neznáme správné škálování
pro Gen2 (Gen1 mělo 0–1023 → 0–53 V, což je jiný hardware).

**Zkalibruj si ho sám dvěma body:**

1. Přidej do TRI řádek s interním senzorem pro napětí, ale se **surovým
   škálováním**: initCalc = 1, initOffset = 0, desetinná místa = 0, mapper
   výstup = vstup přes rozsah 0–4095. Displej ti ukáže holé ADC číslo.
2. Zapalování, motor stojí. Změř multimetrem napětí a zapiš si dvojici
   (raw₁, V₁).
3. Nastartuj, drž 3000 ot/min. Změř znovu → (raw₂, V₂).
4. Spočítej `a = (V₂ − V₁) / (raw₂ − raw₁)` a `b = V₁ − a × raw₁`.
5. Do TRI dej initCalc = a, initOffset = b, desetinná místa = 1.

Dva body stačí, protože dělič napětí je lineární. Měř multimetrem **na
konektoru displeje, ne na baterii** — na vedení k palubovce je úbytek
několik desetin voltu a jinak bys kalibroval i cizí odpor do konstanty.

**Záložní varianta, kdyby interní senzor nefungoval:** MFD15 Gen2 má šest
analogových vstupů. Dělič z 12 V do AIN1 a v TRI sloupec 18 (AIN active).
Licenci Can Switching to nevyžaduje — ta je jen na *vysílání*.

### Řešení pro 5 V: ať si ho převodník změří sám

Tohle je dobrý nápad a stojí to nula součástek. Háček je v tom, že PIC nemůže
změřit vlastní napájení běžným způsobem — ADC měří proti VDD, takže by na
VDD vždycky viděl plný rozsah.

Obchází se to obráceně: **PIC18F25K80 má vestavěnou pevnou napěťovou referenci
(FVR) 1,024 V, kterou umí ADC číst jako vstupní kanál.** Změříš tedy FVR proti
VDD a dopočteš:

```
VDD = 1,024 × 1023 / ADC_výsledek
```

Nula externích součástek, nula pinů. (Ověř si to v datasheetu, až budeme psát
firmware — jsem si tím dost jistý, ale registrové názvy pro K80 sérii chci
mít ověřené, ne po paměti.)

**Do rámců to přidám takhle:** 0x601 má volné bajty 6–7, tak tam půjde
`VddConv` jako `raw × 0,01` = V. Rozsah 4,50–5,50 V, na displeji dvě
desetinná místa.

**A ano, CPU kapacity máš mraky.** PIC18F25K80 na 16 MHz zvládne 4 milion
instrukcí za sekundu. Celý tvůj výpočet — dvě dělení pro spotřebu, jedno
násobení pro výkon, pár klouzavých průměrů — je řádově tisíce instrukcí
za 100 ms rámec. Využití bude v jednotkách procent. Jediné, co je opravdu
těsné, je RAM (3,6 kB) kvůli 30 slotům klouzavého průměru pro dojezd, a i to
je pohodlně v rozpočtu.

---

## Co ještě zbývá ověřit

1. **Trip reset na přístrojovce** — sniff s resetem. Pokud se trip km vysílají,
   naváže se na ně reset průměrné spotřeby. Pokud ne, licence Can Switching.
2. **0x420 b3 = olej, nebo IAT?** — svižná jízda. IAT by spadl, olej ne.
3. **AccelG: podélné, nebo příčné?** — zaparkovat napříč na svahu.
4. **0x288 b5 a b6** — zátěžové, nedekódované. Kandidáti MAF, předstih,
   vstřikovací čas. Nejrychleji porovnáním s měřenými bloky ve VCDS.
5. **Kalibrace ztrátového momentu** — dva body už v logách máme (volnoběh
   a 3000 ot/min v neutrálu), zbývá to dosadit.

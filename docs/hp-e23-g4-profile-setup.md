# HP E23 G4: doporuceny profil a postup aktivace ve Windows

## Co bylo overeno

- K pocitaci jsou pripojeny dva externi monitory `HP E23 G4` s hardware ID `HPN3685`.
- Na verejne dostupnych oficialnich strankach HP jsem dohledal:
  - produktovou stranku `HP E23 G4 FHD Monitor`,
  - dokumentaci `HP Display Center`,
  - navod `HP Displays - Using HP Display Center`, kde je rada `E23 G4` uvedena mezi podporovanymi modely.
- Na verejne indexovanych oficialnich HP strankach jsem nenasel primy `.icm/.icc` soubor ke stazeni specificky pro `HP E23 G4`.

## Doporuceny profil

Jako bezpecny a oficialne podlozeny fallback doporucuji pouzit standardni profil Microsoft:

- `sRGB Color Space Profile.icm`
- lokalni cesta ve Windows:
  - `C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm`

## Proc prave tento profil

- HP u `E23 G4` potvrzuje bezne OSD rizeni barev (`Color`) a podporu konfigurace pres `HP Display Center`.
- Microsoft uvadi, ze pokud zarizeni nema konkretni ICC profil, Windows pouziva systemovy vychozi `sRGB` profil.
- Proto je `sRGB` nejbezpecnejsi volba z oficialnich zdroju, dokud HP neposkytne verejne dohledatelny modelove specificky ICC/ICM profil.

Poznamka:
Toto je informovany zaver z dostupnych oficialnich zdroju, ne potvrzeni, ze HP pro `E23 G4` zadny vlastni ICC profil vubec nevydala.

## Doporucene nastaveni na monitorech pred aktivaci profilu

Na obou monitorech nastavte v OSD stejne hodnoty:

- `Color`: `sRGB` nebo `6500K`
- stejny `Brightness`
- stejny `Contrast`
- vypnout `Low Blue Light` nebo jine obrazove filtry

Bez tohoto kroku se mohou dva kusy stejneho modelu lisit i se stejnym ICC profilem.

## Aktivace profilu pro Monitor 1

1. Stisknete `Win + R`, zadejte `colorcpl` a potvrdte klavesou Enter.
2. V zalozce `Zarizeni` vyberte prvni monitor `HP E23 G4 FHD Monitor`.
3. Zaskrtnete `Pouzit moje nastaveni pro toto zarizeni`.
4. Kliknete na `Pridat...`.
5. Pokud je v seznamu videt `sRGB IEC61966-2.1` nebo `sRGB Color Space Profile.icm`, vyberte jej.
6. Pokud v seznamu neni, kliknete na `Prochazet...` a otevrete:
   `C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm`
7. Po pridani oznacte profil a kliknete na `Nastavit jako vychozi profil`.
8. Otevrete zalozku `Upresnit` a zkontrolujte, ze je profil nastaven pro tento monitor.

## Aktivace profilu pro Monitor 2

1. Ve stejnem okne `Sprava barev` se vratte na zalozku `Zarizeni`.
2. V rozbalovacim seznamu vyberte druhy monitor `HP E23 G4 FHD Monitor`.
3. Znovu zaskrtnete `Pouzit moje nastaveni pro toto zarizeni`.
4. Kliknete na `Pridat...`.
5. Vyberte stejny profil `sRGB IEC61966-2.1` nebo soubor:
   `C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm`
6. Kliknete na `Nastavit jako vychozi profil`.

## Jak overit vysledek

- Otevrete neutralni sedou nebo bilou testovaci plochu.
- Porovnejte oba monitory vedle sebe.
- Pokud se stale lisi bily bod, doladte rucne v OSD hlavne:
  - `Brightness`
  - barevny rezim `sRGB` vs `6500K`
  - pripadne RGB gain, pokud jej monitor nabizi

## Doporuceny dalsi krok pro presnejsi shodu

Pokud chcete opravdu co nejblizsi shodu obou kusu, samotny profil obvykle nestaci. Nejlepsi vysledek da:

- hardwarova kalibrace sondou,
- pro kazdy monitor vlastni ICC profil,
- nasledne prirazeni kazdeho profilu zvlast v `Sprava barev`.

## Zdroje

- HP E23 G4 FHD Monitor: https://support.hp.com/us-en/product/details/hp-e23-g4-fhd-monitor/34513953
- HP Display Center softpaq: https://ftp.hp.com/pub/softpaq/sp114001-114500/sp114078.html
- HP Displays - Using HP Display Center: https://support.hp.com/nz-en/document/ish_5455732-5455779-16
- Microsoft Learn, `Locating ICC Profiles`: https://learn.microsoft.com/windows-hardware/drivers/print/locating-icc-profiles

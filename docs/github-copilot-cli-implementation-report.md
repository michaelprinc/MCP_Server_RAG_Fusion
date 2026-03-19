# GitHub Copilot CLI: implementacni report

## Shrnuti

GitHub Copilot CLI byl na tomto stroji uspesne nainstalovan a technicky overen.
CLI je funkcni a spustitelne z PowerShellu pres prikaz `copilot`.
Autentizace do GitHub Copilot uctu zatim nebyla provedena, protoze v prostredi nebyl k dispozici platny prihlasovaci token a interaktivni login nebyl v ramci teto implementace dokoncen.

## Datum a prostredi

- Datum realizace: `2026-03-19`
- OS shell: `PowerShell 5.1`
- Node.js: `v22.20.0`
- npm: `10.9.3`
- Instalacni metoda: globalni `npm` balicek `@github/copilot`

## Provedene kroky

1. Overeni predpokladu pro instalaci:
   - potvrzen `Node.js 22.x`
   - potvrzen `npm 10.x`
2. Instalace GitHub Copilot CLI:

```powershell
npm.cmd install -g @github/copilot
```

3. Potvrzeni instalacnich wrapperu v globalnim `npm` adresari:
   - `C:\Users\micha\AppData\Roaming\npm\copilot`
   - `C:\Users\micha\AppData\Roaming\npm\copilot.cmd`
   - `C:\Users\micha\AppData\Roaming\npm\copilot.ps1`
4. Prvni inicializace CLI vytvorenim lokalniho adresare:
   - `C:\Users\micha\AppData\Local\copilot`
5. Uprava PowerShell execution policy pouze pro aktualniho uzivatele:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
```

Tento krok byl nutny, protoze puvodni stav `Restricted` blokoval `copilot.ps1` a tim i bezne spousteni prikazu `copilot` primo v PowerShellu.

## Vysledky overeni

Overeni probehlo uspesne v techto bodech:

- `copilot --version`
  - vysledek: `GitHub Copilot CLI 1.0.9`
- `copilot help`
  - vysledek: CLI se korektne spusti a vypise napovedu a dostupne prikazy
- `copilot login --help`
  - vysledek: CLI korektne nabizi podporovany OAuth device flow a tokenove prihlaseni
- `copilot -p "Return exactly OK."`
  - vysledek: prikaz se spusti, ale skonci ocekavanou chybou `No authentication information found`

Zaver:

- instalace je funkcni
- spousteni prikazu `copilot` v PowerShellu je funkcni
- runtime inicializace je funkcni
- funkcni volani modelu zatim ceka na autentizaci uzivatele

## Aktualni stav

GitHub Copilot CLI je pripraven k pouziti.
Pro plnou funkcnost je potreba provest prihlaseni k uctu, ktery ma aktivni GitHub Copilot opravneni.

## Doporuceny dalsi krok: prihlaseni

Nejjednodussi varianta:

```powershell
copilot login
```

CLI spusti OAuth device/browser flow a po dokonceni ulozi token do systemoveho credential store, pripadne do `~/.copilot/`.

Alternativne lze pouzit token v promenne prostredi:

```powershell
$env:COPILOT_GITHUB_TOKEN = "github_pat_..."
copilot
```

Podporovane jsou zejmena:

- `COPILOT_GITHUB_TOKEN`
- `GH_TOKEN`
- `GITHUB_TOKEN`

Poznamka:

- klasicke PAT tokeny `ghp_...` nejsou podporovane
- pro fine-grained PAT je potreba opravneni `Copilot Requests`

## Navod pro dalsi pouzivani

### Interaktivni rezim

Spusteni interaktivniho terminaloveho asistenta:

```powershell
copilot
```

Po prihlaseni lze zadavat dotazy a ukoly primo v terminalu.

### Jednorazovy prompt

Pro neinteraktivni pouziti:

```powershell
copilot -p "Vysvetli strukturu tohoto repozitare" --allow-all-tools
```

Prakticka poznamka:

- v neinteraktivnim rezimu je typicky potreba explicitne povolit pouziti nastroju, jinak CLI nemusi mit dovoleni pracovat se soubory a shellem

### Inicializace instrukci pro repozitar

```powershell
copilot init
```

Tento prikaz pripravi zakladni instrukce pro praci Copilot CLI nad repozitarem.

### Ulozeni sdileneho vystupu do markdown

```powershell
copilot -p "Shrn zmeny v tomto repozitari" --allow-all-tools --share
```

### Napoveda

```powershell
copilot help
copilot login --help
copilot help permissions
copilot help environment
```

## Doporuceni pro bezpecne pouzivani

- Nepouzivejte `--allow-all-tools` rutinne bez rozmyslu v neduveryhodnych repozitarich.
- Pred neinteraktivnimi ukoly si overte, ke kterym adresarum a prikazum ma CLI pristup.
- Pokud budete pouzivat token v promenne prostredi, preferujte docasne nastaveni jen pro aktualni sezeni.

## Zname poznamky z implementace

- Puvodni PowerShell execution policy byla `Restricted`.
- Kvuli tomu byl blokovan jak `copilot`, tak nacitani uzivatelskeho PowerShell profilu.
- Po zmene na `CurrentUser = RemoteSigned` se `copilot` spousti korektne.

## Oficialni reference

- GitHub Docs: https://docs.github.com/en/copilot/how-tos/personal-settings/installing-github-copilot-in-the-cli
- GitHub Docs: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli

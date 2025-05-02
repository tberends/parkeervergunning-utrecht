# 🅿️ Parkeervergunning Utrecht Wachtlijst Tracker

Dit project bevat scripts om informatie over de wachtlijst voor parkeervergunningen in Utrecht te controleren en bij te houden. Het gebruikt slimme verbindingslogica om de website van de gemeente Utrecht te benaderen, via directe verbinding of via proxies indien nodig.

👉 [Bezoek de officiële wachtlijstpagina van de gemeente Utrecht](https://www.utrecht.nl/wonen-en-leven/parkeren/parkeren-bewoner/wachtlijst-parkeervergunning)

## ✨ Status

[![Scrape website, process to csv and commit the file](https://github.com/tberends/parkeervergunning-utrecht/actions/workflows/python-cron.yml/badge.svg)](https://github.com/tberends/parkeervergunning-utrecht/actions/workflows/python-cron.yml)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![Laatst bijgewerkt](https://img.shields.io/github/last-commit/tberends/parkeervergunning-utrecht)

## 📁 Bestanden

- `main.py` - 🚀 Hoofdscript dat automatisch de beste verbindingsmethode vindt, informatie ophaalt over de wachtlijst voor parkeervergunningen en deze opslaat in een CSV-bestand.

## 🔧 Installatie

1. Zorg dat Python 3.6 of hoger is geïnstalleerd.
2. Installeer de benodigde packages:

```bash
pip install requests beautifulsoup4 pandas
```

## 🚀 Gebruik

Het gebruik is nu vereenvoudigd! Je hoeft alleen het hoofdscript uit te voeren:

```bash
python main.py
```

Dit script:
- ✅ Test automatisch of een directe verbinding mogelijk is
- 🔍 Als directe verbinding niet werkt, zoekt het naar werkende proxies
- 📊 Haalt de wachtlijstinformatie op van de website van de gemeente Utrecht
- 💾 Slaat de gegevens op in `data/history.csv` als deze zijn gewijzigd sinds de laatste keer

## 📊 Gegevens

De gegevens worden opgeslagen in `data/history.csv` met de volgende kolommen:
- `record` - Volgnummer
- `bijgewerkt` - Datum waarop de wachtlijst is bijgewerkt
- `aantal_aanmeldingen` - Het aantal mensen op de wachtlijst
- `aanmelddatum_eerstvolgende` - De aanmelddatum van de eerste persoon op de wachtlijst

## ⚙️ Hoe het werkt

Het script probeert eerst een directe verbinding te maken met de website van de gemeente Utrecht. Als dat niet lukt, zoekt het automatisch naar werkende proxies en gebruikt het de snelste beschikbare proxy om de gegevens op te halen.

### Verbindingsproces:

1. 🔄 Test directe verbinding
2. 🔍 Indien nodig, haal lijst met gratis proxies op
3. ⚡ Test de eerste 10 proxies parallel
4. 🥇 Gebruik de snelste werkende verbinding

### Voordelen:

- 🛠️ Volledig automatisch - geen handmatige instellingen nodig
- 🔄 Past zich aan aan veranderende netwerkomstandigheden
- 🚀 Parallel testen van proxies voor optimale snelheid
# SolarEdge V2 Test

Deze testintegratie leest de levenslange zonneproductie via de SolarEdge Monitoring API V2. Home Assistant toont de teller als een aparte energiesensor. De integratie leest elk uur uit.

## Installatie

1. Open **HACS → Add from link** en voeg `https://github.com/Cindyst1/solaredge-v2-test` toe als **Integration**.
2. Download **SolarEdge V2 Test** en herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen → SolarEdge V2 Test** en volg de stappen hieronder vanaf stap 3.

## Handmatige installatie en configuratie

1. Kopieer de map `custom_components/solaredge_v2_test` naar `/config/custom_components/` op je Home Assistant-server.
2. Herstart Home Assistant en kies **Instellingen → Apparaten en diensten → Integratie toevoegen → SolarEdge V2 Test**.
3. Gebruik de Client ID en Client Secret van je SolarEdge-app met **Site Access**, **SITE_DATA** en redirect-URL `http://localhost:8080/oauth/callback`. Vul de eerste productiedatum in als `JJJJ-MM-DD`.
4. Open de aanmeldlink en geef toestemming. Kopieer de hele localhost-URL uit de adresbalk naar het afgeschermde veld in Home Assistant. Een verbindingsfout op localhost is verwacht.
5. Zoek **SolarEdge V2 Test Lifetime Energy** bij de entiteiten en vergelijk de stand met de levenslange opbrengst in de SolarEdge-app. Laat je Energiedashboard tijdens deze test op de bestaande configuratie staan.

De toegang wordt voor één maand aangevraagd. Home Assistant vernieuwt het toegangstoken tijdens die periode en vraagt opnieuw om aanmelding als SolarEdge de toegang intrekt of deze verloopt. Behandel Home Assistant-back-ups als vertrouwelijk, omdat ze de integratiegegevens kunnen bevatten.

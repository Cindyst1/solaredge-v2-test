# SolarEdge V2 Test

Deze testintegratie leest de zonneproductie via de SolarEdge Monitoring API V2. Ze gebruikt eigen entiteiten. Levenslange productie en het laatste kwartiergemiddelde van het vermogen worden elk uur opgevraagd. Productie vandaag, deze maand en dit jaar, de sitestatus en de dagtotalen voor import, export, verbruik en zelfverbruik worden elke zes uur opgevraagd. Dagtotalen worden na middernacht bij de eerstvolgende uurupdate vernieuwd.

Import, export, verbruik en zelfverbruik tonen alleen een waarde als SolarEdge de bijbehorende gegevens levert. Deze test gebruikt SITE_DATA. Apparaatinventaris, batterijmetingen en actuele energiestromen zijn geen onderdeel van deze versie.

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

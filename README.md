# SolarEdge V2 Test

Deze testintegratie leest de zonneproductie via de SolarEdge Monitoring API V2. Ze gebruikt eigen entiteiten. Levenslange productie en het laatste kwartiergemiddelde van het vermogen worden elk uur opgevraagd. Productie vandaag, deze maand en dit jaar, de sitestatus en de dagtotalen voor import, export, verbruik en zelfverbruik worden elke zes uur opgevraagd. Dagtotalen worden na middernacht bij de eerstvolgende uurupdate vernieuwd.

Import, export, verbruik en zelfverbruik tonen alleen een waarde als SolarEdge de bijbehorende gegevens levert.

Voor omvormers en meters kun je bij de bestaande integratie **⋮ → Opnieuw configureren** kiezen. Schakel **Omvormers en meters zoeken (DEVICE_DATA)** in en doorloop de aanmelding opnieuw voor dezelfde installatie. Je SolarEdge-app moet beide scopes toestaan. Elk gevonden record met een serienummer krijgt een diagnostische registratiesensor. Omvormers die SolarEdge als actief markeert, krijgen ook een vermogenssensor met de laatste beschikbare kwartierwaarde.

Met apparaatdetectie aan vraagt de integratie de levenslange productie en vermogensmetingen elke twee uur op. De inventaris en overige waarden worden ongeveer elke twaalf uur bijgewerkt. De integratie probeert ook de laatste energiestromen op te vragen via Advanced Monitoring.

## Installatie

Via **Instellingen → Apparaten en diensten → SolarEdge V2 Test → Configureren** kun je optioneel lokale vermogenssensoren kiezen. Een P1-vermogenssensor met positieve afname en negatieve teruglevering levert netvermogen en netrichting. Kies voor lokaal zonnevermogen de **AC Power**-sensor van je omvormer uit bijvoorbeeld SolarEdge Modbus Multi. Daarmee volgen **Current Power** en **Solar Power Flow** de lokale meting. Ontbreekt een lokale waarde, dan gebruikt de integratie een beschikbare SolarEdge-meting. De P1-optie levert geen zonneproductie of energiedagtotalen.

De omvormer moet via zijn lokale IP-adres bereikbaar zijn en SunSpec Modbus TCP moet ingeschakeld zijn. Bij SetApp is de standaardpoort doorgaans 1502. Laat één Modbus-client de omvormer uitlezen en kies de vermogenssensor van die client in SolarEdge V2 Test.

De entiteiten hieronder komen overeen met de 23 entiteiten van de klassieke SolarEdge-integratie. De energiebalanswaarden zijn dagtotalen. Een entiteit blijft onbekend als de bijbehorende bron ontbreekt. De apparaatlijst wordt momenteel alleen voor omvormers en meters opgevraagd. Voor sensoren, gateways, batterijen en laadniveau zijn er entiteiten zonder ingevulde waarde. Inventaristellingen tellen alleen records die niet expliciet inactief zijn.

| Klassieke SolarEdge-entiteiten | SolarEdge V2 Test |
| --- | --- |
| Lifetime Energy, Energy This Year, Energy This Month, Energy Today | Dezelfde vier productietotalen |
| Current Power, Site Details | Current Power, Site Status |
| Meters, Sensors, Gateways, Batteries, Inverters | Dezelfde vijf inventaristellingen |
| Power Consumption, Solar Power, Grid Power, Stored Power | Home Consumption, Solar, Grid en Battery Power Flow |
| Grid Flow Direction, Storage Flow Direction | Grid en Battery Flow Direction |
| Imported, Produced, Consumed, Self Consumed en Exported Energy | Dezelfde vijf waarden voor vandaag |
| Storage Level | Storage Level |

**Last Reported Site Power** toont de laatste installatiekwartierwaarde uit maximaal elf uur, met het meettijdstip in `sample_at`. **Current Power** toont die waarde alleen als de meting maximaal twee uur oud is. SolarEdge kan toegang tot omvormervermogen en energiestromen afzonderlijk weigeren.

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

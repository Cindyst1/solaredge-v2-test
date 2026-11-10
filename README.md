# SolarEdge V2 Test

SolarEdge V2 Test is een aangepaste Home Assistant-integratie voor de SolarEdge Monitoring API V2. Ze leest zonneopbrengst uit de SolarEdge-cloud. De sensor **Lifetime Energy** kan als zonnebron in het Home Assistant Energiedashboard dienen. De integratie is beschikbaar via HACS als aangepaste repository.

## 1. Installeer via HACS

1. Open **HACS** in Home Assistant.
2. Klik rechtsboven op **⋮ → Aangepaste repositories** (**Custom repositories**).
3. Voeg `https://github.com/Cindyst1/solaredge-v2-test` toe en kies **Integratie** (**Integration**) als categorie.
4. Zoek in HACS naar **SolarEdge V2 Test**, open het resultaat en klik op **Downloaden**.
5. Herstart Home Assistant. Open daarna **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar **SolarEdge V2 Test**.

Zie ook de [HACS-handleiding voor aangepaste repositories](https://www.hacs.xyz/docs/faq/custom_repositories/).

## 2. Koppel je SolarEdge-installatie

1. Maak in het [SolarEdge Developer Platform](https://developer.solaredge.com/) een **Monitoring API**-app aan met toegangstype **Site Access** en scope **SITE_DATA**.
2. Registreer `http://localhost:8080/oauth/callback` als toegestane redirect-URL. Bewaar je **Client ID** en **Client Secret**.
3. Vul in Home Assistant je Client ID, Client Secret en de eerste productiedatum van je installatie in (`JJJJ-MM-DD`).
4. Open op hetzelfde apparaat de aanmeldlink die Home Assistant toont. Kies je SolarEdge-installatie en geef toestemming.
5. Kopieer de volledige `localhost`-URL uit de adresbalk naar het afgeschermde veld in Home Assistant. De browser kan op die URL een verbindingsfout tonen. De URL bevat de tijdelijke aanmeldcode die Home Assistant nodig heeft.

De integratie vraagt toestemming voor één maand en vernieuwt het toegangstoken tijdens die periode. Doorloop de aanmelding opnieuw als Home Assistant daarom vraagt. Houd je Client Secret en de volledige callback-URL privé.

## Welke sensoren leveren een waarde?

| Sensoren | Bron en vereisten |
| --- | --- |
| **Lifetime Energy** | Cumulatieve zonneopbrengst in kWh via **SITE_DATA**. Gebruik deze sensor voor zonneproductie in het Energiedashboard. |
| **Energy Today**, **Produced Energy Today**, **Energy This Month**, **Energy This Year** | Opbrengst over de betreffende periode via **SITE_DATA**. De twee dagsensoren tonen dezelfde productie. |
| **Current Power**, **Solar Power Flow** | Zonnevermogen in W. De cloud levert een kwartierwaarde die maximaal twee uur oud mag zijn. Je kunt ook een bestaande lokale vermogenssensor kiezen. |
| **Last Reported Site Power** | Laatst beschikbare cloudwaarde voor het installatievermogen binnen het zoekvenster van elf uur. Het meettijdstip staat in `sample_at`. |
| **Site Status**, **Imported Energy Today**, **Exported Energy Today**, **Consumed Energy Today**, **Self Consumed Energy Today** | Optionele cloudgegevens. De sensoren krijgen een waarde als SolarEdge die voor je installatie en toegang levert. |
| **Grid Power Flow**, **Grid Flow Direction** | Via een gekozen lokale netvermogenssensor, zoals P1, of via de cloud als Advanced Monitoring energiestromen levert. |
| **Home Consumption Power Flow**, **Battery Power Flow**, **Battery Flow Direction** | Vereisen energiestromen via Advanced Monitoring. SolarEdge kan toegang tot dit onderdeel afzonderlijk weigeren. |
| **Meters**, **Inverters**, registratiestatus per apparaat | Schakel apparaatdetectie in en autoriseer ook **DEVICE_DATA**. De inventaris is afhankelijk van wat SolarEdge voor je site teruggeeft. |
| **Power (15-minute average)** per omvormer | Vereist een omvormer die SolarEdge als actief rapporteert en toegang tot diens vermogensgegevens. Inventaristoegang alleen kan onvoldoende zijn. |
| **Sensors**, **Gateways**, **Batteries**, **Storage Level** | Deze entiteiten hebben in v0.6.1 nog geen databron. |

Een optionele sensor kan **Onbekend** tonen als de bron ontbreekt of SolarEdge toegang weigert. **Lifetime Energy** en het installatievermogen worden elk uur opgevraagd, of elke twee uur met apparaatdetectie. De overige dagtotalen en inventaris worden minder vaak bijgewerkt. De tijd van de laatste cloudmeting kan afwijken van het moment waarop Home Assistant de sensor bijwerkt.

### Apparaatdetectie of een lokale bron toevoegen

- **Omvormers en meters.** Sta **DEVICE_DATA** toe in je SolarEdge-app. Open bij de integratie **⋮ → Opnieuw configureren**, vink **Omvormers en meters zoeken** aan en autoriseer dezelfde installatie opnieuw.
- **Netvermogen.** Open **Configureren** en kies bij **Lokaal netvermogen** een bestaande sensor zoals je P1-meter. Positief betekent afname en negatief betekent teruglevering. Deze keuze levert netvermogen en netrichting. De energiedagtotalen komen via SolarEdge.
- **Zonnevermogen.** Kies bij **Lokaal zonnevermogen** eventueel een bestaande Home Assistant-sensor in W of kW. De integratie leest de gekozen entiteit uit. Voor een installatie die uitsluitend de cloud gebruikt, kun je beide lokale velden leeg laten.

## Energiedashboard

1. Zoek **SolarEdge V2 Test Lifetime Energy** in **Instellingen → Apparaten en diensten → Entiteiten** en vergelijk de tellerstand met de levenslange opbrengst in SolarEdge.
2. Open **Instellingen → Dashboards → Energie** en selecteer **Lifetime Energy** onder **Zonnepanelen**.
3. Gebruik voor dezelfde zonnepanelen één productiebron per periode om dubbeltelling te voorkomen. Als je overstapt van een bestaande sensor en de oude opbrengst in het Energiedashboard wilt behouden, plan dan eerst de overgang van de statistieken. Deze integratie neemt de historie van de oude Home Assistant-sensor niet automatisch over. De levenslange tellerstand bevat wel de opbrengst sinds de opgegeven productiestart.

## Handmatig installeren

Kopieer `custom_components/solaredge_v2_test` uit de [GitHub-release](https://github.com/Cindyst1/solaredge-v2-test/releases/latest) naar `/config/custom_components/`. Herstart Home Assistant, voeg **SolarEdge V2 Test** toe en volg de stappen onder **Koppel je SolarEdge-installatie**.

# SolarEdge V2 Test

[Nederlands](README.md)

SolarEdge V2 Test is a custom Home Assistant integration for the SolarEdge Monitoring API V2. It reads solar production from the SolarEdge cloud. Use **Lifetime Energy** as a solar production source in the Home Assistant Energy dashboard. The integration is available in HACS as a custom repository.

## 1. Install via HACS

1. Open **HACS** in Home Assistant.
2. Select **⋮ → Custom repositories** in the top right.
3. Add `https://github.com/Cindyst1/solaredge-v2-test` and select **Integration** as the category.
4. Search HACS for **SolarEdge V2 Test**, open the result, and select **Download**.
5. Restart Home Assistant. Go to **Settings → Devices & services → Add integration** and search for **SolarEdge V2 Test**.

See the [HACS guide to custom repositories](https://www.hacs.xyz/docs/faq/custom_repositories/).

## 2. Connect your SolarEdge site

1. In the [SolarEdge Developer Platform](https://developer.solaredge.com/), create a **Monitoring API** app with **Site Access** and the **SITE_DATA** scope.
2. Register `http://localhost:8080/oauth/callback` as an allowed redirect URL. Save your **Client ID** and **Client Secret**.
3. In Home Assistant, enter your Client ID, Client Secret, and the date your system first generated power (`YYYY-MM-DD`).
4. Open the sign-in link shown by Home Assistant on the same device. Select your SolarEdge site and approve access.
5. Copy the full `localhost` URL from the browser address bar into the masked field in Home Assistant. The browser may show a connection error. The URL contains the temporary authorization code Home Assistant needs.

The integration requests access for one month and refreshes the access token during that period. Sign in again when Home Assistant prompts you. Keep your Client Secret and the full callback URL private.

## Which sensors report values?

| Sensors | Source and requirements |
| --- | --- |
| **Lifetime Energy** | Cumulative solar production in kWh via **SITE_DATA**. Use this sensor for solar production in the Energy dashboard. |
| **Energy Today**, **Produced Energy Today**, **Energy This Month**, **Energy This Year** | Production for the relevant period via **SITE_DATA**. Both daily sensors report the same production. |
| **Current Power**, **Solar Power Flow** | Solar power in W. The cloud provides a 15-minute reading up to two hours old. You can also select an existing local power sensor. |
| **Last Reported Site Power** | Latest available cloud reading for site power within an eleven-hour lookup window. The reading's timestamp is available in `sample_at`. |
| **Site Status**, **Imported Energy Today**, **Exported Energy Today**, **Consumed Energy Today**, **Self Consumed Energy Today** | Optional cloud data. These sensors report values when SolarEdge makes the data available for your site and permissions. |
| **Grid Power Flow**, **Grid Flow Direction** | From a selected local grid power sensor such as a P1 meter, or from the cloud if Advanced Monitoring provides power flows. |
| **Home Consumption Power Flow**, **Battery Power Flow**, **Battery Flow Direction** | Require power flows from Advanced Monitoring. SolarEdge can deny access to this data separately. |
| **Meters**, **Inverters**, and registration status per device | Enable device discovery and authorize **DEVICE_DATA**. The inventory depends on what SolarEdge returns for your site. |
| **Power (15-minute average)** per inverter | Requires an inverter that SolarEdge reports as active and access to its power data. Inventory access alone may be insufficient. |
| **Sensors**, **Gateways**, **Batteries**, **Storage Level** | These entities have no data source in v0.6.1. |

Optional sensors can show **Unknown** when the source is missing or SolarEdge denies access. The integration requests **Lifetime Energy** and site power hourly, or every two hours with device discovery enabled. It updates the other daily totals and inventory less often. The cloud reading timestamp may differ from the time Home Assistant updates the sensor.

### Enable device discovery or add a local source

- **Inverters and meters.** Allow **DEVICE_DATA** in your SolarEdge app. Open **⋮ → Reconfigure** for the integration, enable inverter and meter discovery, and authorize the same site again.
- **Grid power.** Open **Configure** and select an existing sensor, such as your P1 meter, under **Local grid power**. Positive values mean import and negative values mean export. This supplies grid power and direction. Daily energy totals come from SolarEdge.
- **Solar power.** Under **Local solar power**, you can select an existing Home Assistant sensor in W or kW. The integration reads that entity. For a cloud-only setup, leave both local fields blank.

## Energy dashboard

1. Find **SolarEdge V2 Test Lifetime Energy** under **Settings → Devices & services → Entities** and compare it with the lifetime production shown in SolarEdge.
2. Open **Settings → Dashboards → Energy** and select **Lifetime Energy** under **Solar panels**.
3. Use one production source per period for the same panels to avoid double counting. If you are switching from an existing sensor and want to keep its production history in the Energy dashboard, plan the statistics migration first. This integration does not automatically migrate the old Home Assistant sensor's history. The lifetime counter includes production since the date you entered.

## Install manually

Copy `custom_components/solaredge_v2_test` from the [GitHub release](https://github.com/Cindyst1/solaredge-v2-test/releases/latest) into `/config/custom_components/`. Restart Home Assistant, add **SolarEdge V2 Test**, and follow the steps under **Connect your SolarEdge site**.

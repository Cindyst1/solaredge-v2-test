"""Expose SolarEdge V2 measurements using separate entity identities."""

import math

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DOMAIN

ENERGY_SENSORS = {
    "lifetime_energy": "Lifetime Energy",
    "energy_this_year": "Energy This Year",
    "energy_this_month": "Energy This Month",
    "energy_today": "Energy Today",
    "produced_energy": "Produced Energy Today",
    "imported_energy": "Imported Energy Today",
    "exported_energy": "Exported Energy Today",
    "consumed_energy": "Consumed Energy Today",
    "self_consumed_energy": "Self Consumed Energy Today",
}

INVENTORY_SENSORS = {
    "meters": ("Meters", "METER"),
    "sensors": ("Sensors", None),
    "gateways": ("Gateways", None),
    "batteries": ("Batteries", None),
    "inverters": ("Inverters", "INVERTER"),
}

FLOW_SENSORS = {
    "flow_solar_power": "Solar Power Flow",
    "flow_consumption_power": "Home Consumption Power Flow",
    "flow_grid_power": "Grid Power Flow",
    "flow_battery_power": "Battery Power Flow",
    "flow_grid_power_direction": "Grid Flow Direction",
    "flow_battery_power_direction": "Battery Flow Direction",
}

LOCAL_POWER_SOURCES = {
    "current_power": "local_solar_power",
    "flow_solar_power": "local_solar_power",
    "flow_grid_power": "local_grid_power",
    "flow_grid_power_direction": "local_grid_power",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Register the site measurements."""
    entities = [SolarEdgeSensor(entry, key, name) for key, name in ENERGY_SENSORS.items()]
    entities.extend([
        SolarEdgeSensor(entry, "current_power", "Current Power"),
        SolarEdgeSensor(entry, "last_reported_site_power", "Last Reported Site Power"),
        SolarEdgeSensor(entry, "site_status", "Site Status"),
        SolarEdgeSensor(entry, "storage_level", "Storage Level"),
    ])
    entities.extend(SolarEdgeSensor(entry, key, name) for key, name in FLOW_SENSORS.items())
    entities.extend(
        SolarEdgeSensor(entry, key, name) for key, (name, _) in INVENTORY_SENSORS.items()
    )
    async_add_entities(entities)
    if not entry.data.get("device_inventory"):
        return
    coordinator = entry.runtime_data
    registry = dr.async_get(hass)
    known = set()
    known_power = set()

    @callback
    def add_devices():
        devices = coordinator.data.get("devices") or {}
        site_id = entry.data["site_id"]
        inactive = {
            serial for serial, device in devices.items()
            if device["type"] == "INVERTER" and device.get("active") is False
        }
        for serial in inactive:
            identifier = (DOMAIN, f"{site_id}_{serial}")
            registered = registry.async_get_device(identifiers={identifier})
            if (
                registered is not None
                and registered.identifiers == {identifier}
                and registered.config_entries == {entry.entry_id}
            ):
                registry.async_remove_device(registered.id)
                known.discard(serial)
                known_power.discard(serial)
        new_serials = devices.keys() - inactive - known
        if new_serials:
            known.update(new_serials)
            async_add_entities([
                SolarEdgeInventorySensor(entry, serial, devices[serial])
                for serial in sorted(new_serials)
            ])
        power = coordinator.data.get("inverter_power", {})
        new_power = power.keys() - known_power
        if new_power:
            known_power.update(new_power)
            async_add_entities([
                SolarEdgeInverterPowerSensor(entry, serial, devices[serial])
                for serial in sorted(new_power)
            ])

    entry.async_on_unload(coordinator.async_add_listener(add_devices))
    add_devices()


class SolarEdgeSensor(CoordinatorEntity, SensorEntity):
    """One reading from the SolarEdge monitoring API."""

    def __init__(self, entry, key, name):
        super().__init__(entry.runtime_data)
        self.key = key
        self.local_source = entry.options.get(LOCAL_POWER_SOURCES.get(key))
        self._attr_name = f"SolarEdge V2 Test {name}"
        self._attr_unique_id = f"{entry.data['site_id']}_v2_test_{key}"
        if key in ENERGY_SENSORS:
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
            self._attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        elif key in ("current_power", "last_reported_site_power") or (
            key in FLOW_SENSORS and key.endswith("_power")
        ):
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfPower.WATT
        elif key == "storage_level":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = PERCENTAGE
        elif key in INVENTORY_SENSORS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _inventory_count(self):
        devices = self.coordinator.data.get("devices")
        _, device_type = INVENTORY_SENSORS[self.key]
        if devices is None or device_type is None:
            return None
        return sum(
            device["type"] == device_type and device.get("active") is not False
            for device in devices.values()
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if self.local_source:
            self.async_on_remove(async_track_state_change_event(
                self.hass, [self.local_source], self._local_power_changed
            ))

    @callback
    def _local_power_changed(self, event):
        self.async_write_ha_state()

    def _local_watts(self):
        if not self.local_source:
            return None
        state = self.hass.states.get(self.local_source)
        if state is None:
            return None
        factor = {"W": 1, "kW": 1000, "MW": 1000000}.get(
            state.attributes.get("unit_of_measurement")
        )
        if factor is None:
            return None
        try:
            watts = float(state.state) * factor
        except ValueError:
            return None
        if not math.isfinite(watts):
            return None
        if self.key in ("current_power", "flow_solar_power") and watts < 0:
            return None
        return watts

    @property
    def available(self):
        return self._local_watts() is not None or super().available

    @property
    def native_value(self):
        """Return the latest reading, if supplied by SolarEdge."""
        local = self._local_watts()
        if local is not None:
            if self.key == "flow_grid_power_direction":
                return "import" if local > 0 else "export" if local < 0 else "idle"
            return abs(local) if self.key == "flow_grid_power" else local
        if self.key == "current_power":
            return self.coordinator.data.get("fresh_site_power")
        if self.key == "last_reported_site_power":
            sample = self.coordinator.data.get("current_power")
            return sample[0] if sample is not None else None
        if self.key == "produced_energy":
            return self.coordinator.data.get("energy_today")
        if self.key in INVENTORY_SENSORS:
            return self._inventory_count()
        return self.coordinator.data.get(self.key)

    @property
    def extra_state_attributes(self):
        if self._local_watts() is not None:
            return {"source_entity": self.local_source}
        if self.key == "current_power" and "fresh_site_power" in self.coordinator.data:
            return {"sample_at": self.coordinator.data["current_power"][1]}
        if self.key == "last_reported_site_power":
            sample = self.coordinator.data.get("current_power")
            if sample is not None:
                return {"sample_at": sample[1]}
        return None


class SolarEdgeInventorySensor(CoordinatorEntity, SensorEntity):
    """Show the registration state of a SolarEdge inventory record."""

    _attr_has_entity_name = True
    _attr_name = "Monitoring registration"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, serial, device):
        super().__init__(entry.runtime_data)
        self.serial = serial
        site_id = entry.data["site_id"]
        self._attr_unique_id = f"{site_id}_inventory_{serial}"
        model = device.get("partNumber")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{site_id}_{serial}")},
            name=device.get("name") or model or f"SolarEdge {device['type'].title()}",
            manufacturer=device.get("manufacturer") or "SolarEdge",
            model=model,
            serial_number=serial,
        )

    @property
    def native_value(self):
        """Report the API flag, which describes registration rather than output."""
        devices = self.coordinator.data.get("devices")
        if devices is None:
            return None
        device = devices.get(self.serial)
        if device is None:
            return "not_listed"
        active = device.get("active")
        if isinstance(active, bool):
            return "active" if active else "inactive"
        return "listed"


class SolarEdgeInverterPowerSensor(SolarEdgeInventorySensor):
    """Latest reported quarter-hour power of an active inverter."""

    _attr_name = "Power (15-minute average)"
    _attr_entity_category = None
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, entry, serial, device):
        super().__init__(entry, serial, device)
        self._attr_unique_id = f"{entry.data['site_id']}_inverter_power_{serial}"

    @property
    def native_value(self):
        sample = self.coordinator.data.get("inverter_power", {}).get(self.serial)
        return sample[0] if sample is not None else None

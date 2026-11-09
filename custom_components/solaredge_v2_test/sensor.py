"""Expose SolarEdge V2 measurements using separate entity identities."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DOMAIN

ENERGY_SENSORS = {
    "lifetime_energy": "Lifetime Energy",
    "energy_this_year": "Energy This Year",
    "energy_this_month": "Energy This Month",
    "energy_today": "Energy Today",
    "imported_energy": "Imported Energy Today",
    "exported_energy": "Exported Energy Today",
    "consumed_energy": "Consumed Energy Today",
    "self_consumed_energy": "Self Consumed Energy Today",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Register the site measurements."""
    entities = [SolarEdgeSensor(entry, key, name) for key, name in ENERGY_SENSORS.items()]
    entities.extend([
        SolarEdgeSensor(entry, "current_power", "Current Power"),
        SolarEdgeSensor(entry, "site_status", "Site Status"),
    ])
    async_add_entities(entities)
    if not entry.data.get("device_inventory"):
        return
    coordinator = entry.runtime_data
    known = set()

    @callback
    def add_devices():
        devices = coordinator.data.get("devices") or {}
        new_serials = devices.keys() - known
        if new_serials:
            known.update(new_serials)
            async_add_entities([
                SolarEdgeInventorySensor(entry, serial, devices[serial])
                for serial in sorted(new_serials)
            ])

    entry.async_on_unload(coordinator.async_add_listener(add_devices))
    add_devices()


class SolarEdgeSensor(CoordinatorEntity, SensorEntity):
    """One reading from the SolarEdge monitoring API."""

    def __init__(self, entry, key, name):
        super().__init__(entry.runtime_data)
        self.key = key
        self._attr_name = f"SolarEdge V2 Test {name}"
        self._attr_unique_id = f"{entry.data['site_id']}_v2_test_{key}"
        if key in ENERGY_SENSORS:
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
            self._attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        elif key == "current_power":
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the latest reading, if supplied by SolarEdge."""
        return self.coordinator.data.get(self.key)


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

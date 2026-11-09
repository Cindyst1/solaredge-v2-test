"""Expose SolarEdge V2 measurements using separate entity identities."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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

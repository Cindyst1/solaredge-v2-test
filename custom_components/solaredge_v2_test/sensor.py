"""Expose the V2 lifetime reading under a separate sensor identity."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.update_coordinator import CoordinatorEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Register the test sensor."""
    async_add_entities([LifetimeEnergy(entry)])


class LifetimeEnergy(CoordinatorEntity, SensorEntity):
    """Lifetime PV production reported by the SolarEdge cloud."""

    _attr_name = "SolarEdge V2 Test Lifetime Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, entry):
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.data['site_id']}_v2_test_lifetime_energy"

    @property
    def native_value(self):
        """Return the last successful lifetime reading."""
        return self.coordinator.data

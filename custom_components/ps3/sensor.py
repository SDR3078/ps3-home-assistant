from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .const import DOMAIN, ENTRIES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [
            TempSensor(
                hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], "cpu_temp"
            ),
            TempSensor(
                hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], "rsx_temp"
            ),
            FanSpeedSensor(
                hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], "fan_speed"
            ),
        ]
    )


class TempSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name

    @property
    def name(self):
        return f"PS3_{self._name}"

    @property
    def state(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self._name)
        return None

    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS


class FanSpeedSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._icon = "mdi:fan"

    @property
    def name(self):
        return f"PS3_{self._name}"

    @property
    def state(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self._name)
        return None

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def icon(self):
        return self._icon

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE

from .const import DOMAIN, ENTRIES, MAX_FAN_SPEED, MIN_FAN_SPEED, FAN_SPEED_INCREASE
from .API.exceptions import SensorError, RequestError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [FanSpeed(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"])]
    )

class FanSpeed(NumberEntity, CoordinatorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._icon = "mdi:fan"

    @property
    def name(self):
        return "PS3 Fan Speed"

    @property
    def native_max_value(self):
        return MAX_FAN_SPEED
    
    @property
    def native_min_value(self):
        return MIN_FAN_SPEED
    
    @property
    def native_step(self):
        return FAN_SPEED_INCREASE
    
    @property
    def native_value(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get("fan_speed")
        return None
    
    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE
    
    @property
    def icon(self):
        return self._icon
    
    async def async_set_native_value(self, fan_speed: int):
        try:
            await self.coordinator.wrapper.set_fan_speed(fan_speed)
            await self.coordinator.async_refresh()
        except SensorError as e:
            _LOGGER.error(f"Error updating data: {e}")
        except RequestError as e:
            _LOGGER.error(e)


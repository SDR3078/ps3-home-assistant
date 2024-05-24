from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, ENTRIES, MAX_FAN_SPEED, MIN_FAN_SPEED, FAN_SPEED_INCREASE, FAN_SPEED_KEY, NAME, MANUFACTURER
from .helpers import request

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [FanSpeed(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], config_entry.data.get('mac_address'))]
    )

class FanSpeed(NumberEntity, CoordinatorEntity):
    def __init__(self, coordinator, mac_address):
        super().__init__(coordinator)
        self._mac_address = mac_address

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
        if self.state is None:
            return "mdi:fan-off"
        else:
            return "mdi:fan"
    
    @property
    def unique_id(self):
        return f"{self._mac_address}-{FAN_SPEED_KEY}"
    
    @property
    def device_info(self):
        return DeviceInfo(
            identifiers = {
                (DOMAIN, self._mac_address)
            },
            name = NAME,
            model = NAME,
            manufacturer = MANUFACTURER,
            sw_version = self.coordinator.data.get("firmware_version")
        )
    
    @request
    async def async_set_native_value(self, fan_speed: int):
        await self.coordinator.wrapper.set_fan_speed(fan_speed)
        await self.coordinator.async_refresh()


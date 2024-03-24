from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity, HVACMode, ClimateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, ENTRIES, MAX_TEMP, MIN_TEMP
from .API.PS3MAPI import FanModeError, SensorError, RequestError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [TempRegulator(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], "cpu_temp")]
    )


class TempRegulator(ClimateEntity, CoordinatorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

    @property
    def name(self):
        return f"test"

    @property
    def current_temperature(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self._name)
        return None
    
    @property
    def fan_mode(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get("fan_mode")
        return None

    @property
    def fan_modes(self):
        return self.coordinator.wrapper.fan_modes
    
    @property
    def hvac_mode(self):
        if self.coordinator.data is not None:
            if self.coordinator.data.get("fan_mode") is not None:
                return HVACMode.COOL
        return HVACMode.OFF
    
    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.COOL]
    
    @property
    def max_temp(self):
        return float(MAX_TEMP)
    
    @property
    def min_temp(self):
        return float(MIN_TEMP)
    
    @property
    def target_temperature(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get("target_temp")
        return None
    
    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS
    
    async def async_set_fan_mode(self, fan_mode):
        try:
            await self.coordinator.wrapper.set_fan_mode(fan_mode)
            await self.coordinator.async_refresh()
        except FanModeError as e:
            _LOGGER.error(e)
        except SensorError as e:
            _LOGGER.error(f"Error updating data: {e}")

    async def async_set_temperature(self, **kwargs):
        try:
            await self.coordinator.wrapper.set_target_temp(kwargs.get("temperature"))
            await self.coordinator.async_refresh()
        except FanModeError as e:
            _LOGGER.error(e)
        except SensorError as e:
            _LOGGER.error(f"Error updating data: {e}")
        except RequestError as e:
            _LOGGER.error(e)

    async def async_set_hvac_mode(self, hvac_mode):
        await self.coordinator.async_refresh()
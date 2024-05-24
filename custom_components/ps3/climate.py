from __future__ import annotations

import logging
import asyncio
import aiohttp

from homeassistant.components.climate import ClimateEntity, HVACMode, ClimateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry

from .const import MAX_TEMP, MIN_TEMP, DOMAIN, ENTRIES, SCRIPT_DOMAIN, TURN_ON_SCRIPT, SYSTEM_TEMP_KEY, NAME, MANUFACTURER
from .helpers import request

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [TempRegulator(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], config_entry.data.get(TURN_ON_SCRIPT), hass.services, config_entry.data.get('mac_address'))]
    )


class TempRegulator(ClimateEntity, CoordinatorEntity):
    _enable_turn_on_off_backwards_compatibility = False
    
    def __init__(self, coordinator, turn_on_script, service_registry, mac_address):
        super().__init__(coordinator)
        self._turn_on_script = turn_on_script
        self._service_registry = service_registry
        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | (ClimateEntityFeature.TURN_ON if turn_on_script is not None else 0)
        )
        self._mac_address = mac_address

    @property
    def extra_state_attributes(self):
        if self.coordinator.data is not None:
            rsx_temp = self.coordinator.data.get("rsx_temp")
            cpu_temp = self.coordinator.data.get("cpu_temp")
        else:
            rsx_temp = None
            cpu_temp = None
        
        return {"cpu_temp": cpu_temp, "rsx_temp": rsx_temp}
            
    @property
    def name(self):
        return "PS3 System Temperature"

    @property
    def current_temperature(self):
        if self.coordinator.data is not None:
            rsx_temp = self.coordinator.data.get("rsx_temp")
            cpu_temp = self.coordinator.data.get("cpu_temp")
            if rsx_temp and cpu_temp:
                return max(cpu_temp, rsx_temp)
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
    
    @property
    def icon(self):
        if self.hvac_mode == HVACMode.OFF:
            return "mdi:snowflake-off"
        else:
            return "mdi:snowflake"
    
    @property
    def unique_id(self):
        return f"{self._mac_address}-{SYSTEM_TEMP_KEY}"
    
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
    async def async_set_fan_mode(self, fan_mode):
        await self.coordinator.wrapper.set_fan_mode(fan_mode)
        await self.coordinator.async_refresh()

    @request
    async def async_set_temperature(self, **kwargs):
        await self.coordinator.wrapper.set_target_temp(kwargs.get("temperature"))
        await self.coordinator.async_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode == HVACMode.COOL:
            await self.async_turn_on()
        else:
            raise HomeAssistantError(f"{hvac_mode} not recognized")

    @request
    async def async_turn_off(self):
        await self.coordinator.wrapper.shutdown()
        await self.coordinator.async_refresh()

    async def async_turn_on(self, timeout = 60):
        if self.coordinator.startup_lock.locked():
            raise ServiceValidationError(
                translation_domain = DOMAIN,
                translation_key = "starting_up"
            )

        else:
            async def wait_with_timeout(self):
                while True:
                    try:
                        await self.coordinator.wrapper.wait_for_xmb()
                        break
                    except Exception:
                        pass
            
            async with self.coordinator.startup_lock:
                await self._service_registry.async_call(SCRIPT_DOMAIN, self._turn_on_script, blocking = True)
                try:
                    await asyncio.wait_for(wait_with_timeout(self), timeout)
                except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
                    raise HomeAssistantError(e)

            await self.coordinator.async_refresh()

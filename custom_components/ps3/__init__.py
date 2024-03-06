from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .API.PS3MAPI import PS3MAPIWrapper, SensorError
from .const import CONF_ENTRY_ID, ENTRIES, DATA_HASS_CONFIG, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    
    # Store full yaml config in data for platform.NOTIFY
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_HASS_CONFIG] = config

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(ENTRIES, {})

    coordinator = PS3Coordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][ENTRIES][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {CONF_NAME: DOMAIN, CONF_ENTRY_ID: entry.entry_id},
            hass.data[DOMAIN][DATA_HASS_CONFIG],
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN][ENTRIES].pop(entry.entry_id)

    return unload_ok


class PS3Coordinator(DataUpdateCoordinator):
    """Class to handle updates from PS3"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize data update coordinator."""
        self.ip_address = config_entry.data.get("ip_address")
        self.wrapper = PS3MAPIWrapper(self.ip_address)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        try:
            await self.wrapper.update()
            return {
                "state": self.wrapper.state,
                "cpu_temp": self.wrapper.cpu_temp,
                "rsx_temp": self.wrapper.rsx_temp,
                "fan_speed": self.wrapper.fan_speed,
            }
        except SensorError as e:
            _LOGGER.error(f"Error updating data: {e}")
            return None

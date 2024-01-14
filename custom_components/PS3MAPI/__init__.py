from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .API.PS3MAPI import PS3MAPIWrapper, SensorError
from .const import DOMAIN, PLATFORMS

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER = logging.getLogger(__name__)

    ip_address = entry.data.get("ip_address")
    wrapper = PS3MAPIWrapper(ip_address)

    async def _async_update_data():
        try:
            await wrapper.update()
            return {
                "state": wrapper.state,
                "cpu_temp": wrapper.cpu_temp,
                "rsx_temp": wrapper.rsx_temp,
                "fan_speed": wrapper.fan_speed,
            }
        except SensorError as e:
            _LOGGER.error(f"Error updating data: {e}")
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="PS3MAPIWrapper",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=30),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}
    await hass.data[DOMAIN][entry.entry_id]["coordinator"].async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

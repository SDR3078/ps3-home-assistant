from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .API.PS3MAPI import PS3MAPIWrapper

DOMAIN = 'PS3MAPI'

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:

    _LOGGER = logging.getLogger(__name__)

    ip_address = config[DOMAIN].get('ip_address')
    wrapper = PS3MAPIWrapper(ip_address)

    async def _async_update_data():
        try:
            await wrapper.update()
            return {'state': wrapper.state, 'cpu_temp': wrapper.cpu_temp, 'rsx_temp': wrapper.rsx_temp, 'fan_speed': wrapper.fan_speed}
        except Exception as e:
            _LOGGER.error(f"Error updating data: {e}")
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name = "PS3MAPIWrapper",
        update_method = _async_update_data,
        update_interval = timedelta(seconds=30)
    )

    hass.data[DOMAIN] = {'coordinator': coordinator}
    await hass.data[DOMAIN]['coordinator'].async_refresh()

    platforms = ['binary_sensor', 'sensor']

    for platform in platforms:
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)

    return True
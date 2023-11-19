"""Example Load Platform integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = 'PS3MAPI'


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    ip_address = config[DOMAIN].get('ip_address')
    hass.helpers.discovery.load_platform('binary_sensor', DOMAIN, {'ip_address': ip_address}, config)

    return True
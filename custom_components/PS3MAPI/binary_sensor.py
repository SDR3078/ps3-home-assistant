from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity
from .API.PS3MAPI import PS3MAPIWrapper
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

def setup_platform(hass: HomeAssistant, config: ConfigType, add_entities: AddEntitiesCallback, discovery_info: DiscoveryInfoType):
    ip_address = discovery_info.get('ip_address')
    wrapper = PS3MAPIWrapper(ip_address)
    add_entities([OnOffSensor(wrapper)], update_before_add = True)

class OnOffSensor(BinarySensorEntity):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self._state = None

    async def async_update(self):
        await self.wrapper.update()
        if self.wrapper.state == 'On':
            self._state = True
        else:
            self._state = False

    @property
    def name(self):
        return "PS3"

    @property
    def is_on(self):
        return self._state
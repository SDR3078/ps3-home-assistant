from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback, discovery_info: DiscoveryInfoType):
    async_add_entities([OnOffSensor(hass.data['PS3MAPI']['coordinator'])])

class OnOffSensor(BinarySensorEntity, CoordinatorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def name(self):
        return "PS3"

    @property
    def is_on(self):
        if self.coordinator.data['state'] == 'On':
            return True
        else:
            return False
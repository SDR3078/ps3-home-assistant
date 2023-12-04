from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE

async def async_setup_platform(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback, discovery_info: DiscoveryInfoType):
    async_add_entities([TempSensor(hass.data['PS3MAPI']['coordinator'], 'cpu_temp'),
                        TempSensor(hass.data['PS3MAPI']['coordinator'], 'rsx_temp'),
                        FanSpeedSensor(hass.data['PS3MAPI']['coordinator'], 'fan_speed')
                        ])

class TempSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name

    @property
    def name(self):
        return f"PS3_{self._name}"

    @property
    def state(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self._name)
        return None

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

class FanSpeedSensor(SensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._name = name
        self._icon = 'mdi:fan'

    @property
    def name(self):
        return f"PS3_{self._name}"

    @property
    def state(self):
        if self.coordinator.data is not None:
            return self.coordinator.data.get(self._name)
        return None

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def icon(self):
        return self._icon
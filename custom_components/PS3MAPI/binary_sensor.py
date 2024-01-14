from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [OnOffSensor(hass.data[DOMAIN][config_entry.entry_id]["coordinator"])]
    )


class OnOffSensor(BinarySensorEntity, CoordinatorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def name(self):
        return "PS3"

    @property
    def is_on(self):
        if self.coordinator.data["state"] == "On":
            return True
        else:
            return False

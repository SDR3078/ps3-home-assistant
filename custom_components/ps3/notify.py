"""PS3 Notify service."""
from __future__ import annotations

from homeassistant.components.notify import ATTR_TARGET, BaseNotificationService
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .API.PS3MAPI import PS3MAPIWrapper, NotificationError

from .const import CONF_ENTRY_ID, DOMAIN


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> PS3NotificationService | None:
    """Get the PS3 notification service."""
    if discovery_info is None:
        return None

    data = hass.data[DOMAIN][(discovery_info or {})[CONF_ENTRY_ID]]["coordinator"]
    return PS3NotificationService(data.wrapper)


class PS3NotificationService(BaseNotificationService):
    """Implement the notification service for the PS3."""

    def __init__(self, ps3wrapper) -> None:
        """Initialize the service."""
        self.ps3wrapper = ps3wrapper

    async def async_send_message(self, message="", **kwargs):
        """Send a message."""
        try:
            await self.ps3wrapper.send_notification(message)
        except NotificationError:
            raise

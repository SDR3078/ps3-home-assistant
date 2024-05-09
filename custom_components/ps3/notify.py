"""PS3 Notify service."""
from __future__ import annotations

import logging

from collections import defaultdict

from homeassistant.components.notify import ATTR_TARGET, ATTR_DATA, BaseNotificationService
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .API.exceptions import NotificationError

from .const import DOMAIN, ENTRIES

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> PS3NotificationService | None:
    """Get the PS3 notification service."""
    if discovery_info is None:
        return None

    wrapper_dict = {entry['coordinator'].ip_address: entry['coordinator'].wrapper for entry in hass.data[DOMAIN][ENTRIES].values()}
    return PS3NotificationService(wrapper_dict)


class PS3NotificationService(BaseNotificationService):
    """Implement the notification service for the PS3."""

    def __init__(self, wrapper_dict) -> None:
        """Initialize the service."""
        self.wrapper_dict= wrapper_dict

    async def async_send_message(self, message="", **kwargs):
        """Send a message."""
        
        targets = kwargs.get(ATTR_TARGET)

        data = kwargs.get(ATTR_DATA)

        if not targets:
            _LOGGER.error("No targets specified for PS3 notify service")
        else:
            for target in targets:
                try:
                    if data:
                        data_dict = defaultdict(lambda: 1, data)
                        await self.wrapper_dict[target].send_notification(message, icon = data_dict['icon'], sound = data_dict['sound'])
                    else:
                        await self.wrapper_dict[target].send_notification(message)
                except KeyError:
                    _LOGGER.error(f"{target} is not a known ip address of a registered PlayStation® 3 device")
                except NotificationError:
                    _LOGGER.warning(f"Message could not be send because {target} is unavailable")

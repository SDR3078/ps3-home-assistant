from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant

from .PS3MAPI import PS3MAPIWrapper, NotificationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict):
    wrapper = PS3MAPIWrapper(data[CONF_IP_ADDRESS])

    try:
        await wrapper.send_notification("Home Assistant connection was succesful!")
    except NotificationError:
        raise CannotConnect

    return {"title": data[CONF_IP_ADDRESS]}


class PS3MAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                _LOGGER.error("Cannot Connect")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

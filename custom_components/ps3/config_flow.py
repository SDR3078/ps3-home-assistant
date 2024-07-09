from __future__ import annotations

import logging
import asyncio

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
from homeassistant.helpers.device_registry import format_mac

from .API.PS3MAPI import PS3MAPIWrapper
from .const import DOMAIN, TURN_ON_SCRIPT

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict):
    wrapper = PS3MAPIWrapper(data[CONF_IP_ADDRESS])

    try:
        mac_address = format_mac(await wrapper.get_mac_address())
        asyncio.sleep(0)
        await wrapper.send_notification("Home Assistant connection was succesful!")
    except Exception:
        raise CannotConnect

    return mac_address


class PS3MAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input = None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            try:
                mac_address = await validate_input(self.hass, user_input)
                return self.async_create_entry(title = user_input[CONF_IP_ADDRESS], data = {**user_input, "mac_address": mac_address})
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
                    vol.Optional(TURN_ON_SCRIPT): SelectSelector(
                        SelectSelectorConfig(
                            options = [value.unique_id for value in self.hass.data["entity_registry"].entities.values() if value.platform == 'script'], 
                            mode = SelectSelectorMode.DROPDOWN
                            )
                        )
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

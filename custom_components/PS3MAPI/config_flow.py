from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS

from .const import DOMAIN


class PS3MAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_IP_ADDRESS], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): str,
                }
            ),
            errors=errors,
        )

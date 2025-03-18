from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN, DEFAULT_NAME

import voluptuous as vol

# Basic schema for manual configuration
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
})


class AmbiSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AmbiSense."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Set this as the unique ID
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"AmbiSense ({user_input[CONF_HOST]})",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )

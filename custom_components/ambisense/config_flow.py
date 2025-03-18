"""Config flow for AmbiSense integration with mDNS discovery."""
import asyncio
import logging
import aiohttp
import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.network import get_mdns

from . import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)

class AmbiSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AmbiSense."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    
    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        # Try to discover devices first
        try:
            if user_input is None:  # Only discover if no input yet
                self._discovered_devices = await self._discover_devices()
                
                # If discovered devices exist, show discovery step
                if self._discovered_devices:
                    return await self.async_step_device_selection()
        except Exception as e:
            _LOGGER.error(f"Discovery error: {e}")
            # Continue with manual entry if discovery fails

        # Manual configuration
        if user_input is not None:
            try:
                # Set this as the unique ID
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                # Try to connect to validate
                info = await self._validate_input(user_input)
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )

    async def async_step_device_selection(self, user_input=None):
        """Handle device selection step after discovery."""
        if user_input is not None:
            selected_device = user_input.get('device')
            if selected_device:
                # Get the IP for the selected device
                host = self._discovered_devices[selected_device]
                
                try:
                    # Try to connect to validate
                    info = await self._validate_input({
                        CONF_HOST: host, 
                        CONF_NAME: selected_device
                    })
                    
                    # Create configuration entry
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=info["title"],
                        data={
                            CONF_HOST: host,
                            CONF_NAME: selected_device
                        }
                    )
                except CannotConnect:
                    return self.async_show_form(
                        step_id="device_selection",
                        data_schema=vol.Schema({
                            vol.Required('device'): vol.In(list(self._discovered_devices.keys()))
                        }),
                        errors={"base": "cannot_connect"}
                    )
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    return self.async_show_form(
                        step_id="device_selection",
                        data_schema=vol.Schema({
                            vol.Required('device'): vol.In(list(self._discovered_devices.keys()))
                        }),
                        errors={"base": "unknown"}
                    )
        
        # Show discovered devices
        return self.async_show_form(
            step_id="device_selection",
            data_schema=vol.Schema({
                vol.Required('device'): vol.In(list(self._discovered_devices.keys()))
            }),
            description_placeholders={
                "devices": "\n".join(self._discovered_devices.keys())
            }
        )
        
    async def _discover_devices(self):
    """Discover AmbiSense devices on the network."""
    discovered_devices = {}
    
    try:
        # First try to discover devices via mDNS browsing
        zc = await get_mdns(self.hass)
        
        # Use "_http._tcp.local." for general HTTP devices
        # We'll filter for "ambisense" in the name
        service_type = "_http._tcp.local."
        
        results = await zc.async_browse(service_type)
        
        for result in results:
            try:
                # Only process results that match our naming pattern
                if "ambisense" in result.name.lower():
                    info = await zc.async_get_service_info(service_type, result.name)
                    
                    if info and info.addresses:
                        hostname = result.name.rstrip(".local.")
                        
                        # Extract IPv4 addresses
                        ipv4_addresses = []
                        for addr in info.addresses:
                            try:
                                # Convert bytes to string if necessary
                                if isinstance(addr, bytes):
                                    import socket
                                    addr = socket.inet_ntoa(addr)
                                
                                # Check if this looks like an IPv4 address
                                if len(addr.split(".")) == 4:
                                    ipv4_addresses.append(addr)
                            except Exception:
                                continue
                                
                        if ipv4_addresses:
                            discovered_devices[hostname] = ipv4_addresses[0]
            except Exception as e:
                _LOGGER.error(f"Error processing discovery result {result.name}: {e}")
                continue
        
        # Additional fallback: Try to directly resolve common ambisense hostnames
        # This can help if browsing failed but we know the naming pattern
        common_locations = ["livingroom", "bedroom", "kitchen", "home", "office"]
        for location in common_locations:
            hostname = f"ambisense-{location}.local"
            try:
                import socket
                addr_info = await self.hass.async_add_executor_job(
                    socket.gethostbyname, hostname
                )
                if addr_info:
                    discovered_devices[hostname.rstrip(".local")] = addr_info
            except Exception:
                # Just skip if can't resolve
                pass
                
    except Exception as e:
        _LOGGER.error(f"Discovery error: {e}")
    
    return discovered_devices

import traceback

class AmbiSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self):
        """Initialize the config flow."""
        super().__init__()
        self._errors = {}

    async def async_step_user(self, user_input=None):
        try:
            # Existing implementation
            pass
        except Exception as e:
            _LOGGER.error(f"Config flow error: {e}")
            _LOGGER.error(traceback.format_exc())
            self._errors["base"] = "unknown"

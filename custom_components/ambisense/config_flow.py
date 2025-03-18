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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.zeroconf import ZeroconfServiceInfo
from zeroconf.asyncio import AsyncServiceInfo

from . import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class AmbiSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AmbiSense."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    
    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle zeroconf discovery."""
        # Check if this is our device
        hostname = discovery_info.hostname
        if not hostname.startswith("ambisense-"):
            return self.async_abort(reason="not_ambisense_device")

        # Extract name and IP address
        name = hostname.replace(".local.", "")
        host = discovery_info.host
        
        # Set unique ID
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()
        
        # Store discovered device info
        self.context["title_placeholders"] = {"name": name}
        
        # Setup discovery info for the next step
        self._discovered_devices = {name: host}
        
        return await self.async_step_discovery_confirm()
        
    async def async_step_discovery_confirm(self, user_input=None):
        """Handle confirmation of discovered device."""
        if user_input is not None:
            name = list(self._discovered_devices.keys())[0]
            host = self._discovered_devices[name]
            
            try:
                info = await self._validate_input({
                    CONF_HOST: host,
                    CONF_NAME: name
                })
                
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: host,
                        CONF_NAME: name
                    }
                )
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            except Exception:
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
                
        name = list(self._discovered_devices.keys())[0]
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": name},
            data_schema=vol.Schema({})
        )

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
            from zeroconf import ServiceBrowser, Zeroconf
            from zeroconf.asyncio import AsyncZeroconf

            async_zc = AsyncZeroconf()
            service_types = ["_http._tcp.local."]
            
            for service_type in service_types:
                services = await async_zc.async_browse(service_type)
                
                for service in services:
                    if not service.name.startswith("ambisense-"):
                        continue
                    
                    info = AsyncServiceInfo(service_type, service.name)
                    await info.async_request(async_zc.zeroconf, 3000)
                    
                    if info and info.addresses:
                        hostname = service.name.replace(".local.", "")
                        
                        # Extract the first IPv4 address
                        for addr in info.addresses:
                            ip_addr = ".".join(str(ord(byte)) for byte in addr) if isinstance(addr, bytes) else addr
                            discovered_devices[hostname] = ip_addr
                            break
            
            await async_zc.async_close()
            
            # Additional fallback: Try to directly resolve common ambisense hostnames
            common_locations = ["livingroom", "bedroom", "kitchen", "home", "office"]
            for location in common_locations:
                hostname = f"ambisense-{location}"
                try:
                    import socket
                    addr_info = await self.hass.async_add_executor_job(
                        socket.gethostbyname, f"{hostname}.local"
                    )
                    if addr_info:
                        discovered_devices[hostname] = addr_info
                except Exception:
                    # Just skip if can't resolve
                    pass
                    
        except Exception as e:
            _LOGGER.error(f"Discovery error: {e}")
        
        return discovered_devices
    
    async def _validate_input(self, data):
        """Validate the user input allows us to connect."""
        host = data[CONF_HOST]
        name = data.get(CONF_NAME, DEFAULT_NAME)
        
        # Verify that we can connect to the device
        session = async_get_clientsession(self.hass)
        
        try:
            # First try settings endpoint
            settings_url = f"http://{host}/settings"
            async with session.get(settings_url, timeout=10) as response:
                if response.status != 200:
                    raise CannotConnect
                
                # Try to parse response as JSON
                await response.json()
                
        except (asyncio.TimeoutError, aiohttp.ClientError, ValueError):
            # If settings fails, try distance endpoint
            try:
                distance_url = f"http://{host}/distance"
                async with session.get(distance_url, timeout=10) as response:
                    if response.status != 200:
                        raise CannotConnect
            except (asyncio.TimeoutError, aiohttp.ClientError):
                raise CannotConnect
            
        # If we get here, the connection was successful
        return {
            "title": name
        }

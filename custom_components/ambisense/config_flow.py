"""Config flow for AmbiSense integration with mDNS discovery."""
import asyncio
import logging
import aiohttp
import voluptuous as vol
import zeroconf
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
        vol.Optional(CONF_HOST, description={"suggested_value": "ambisense-{location}.local"}): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)

class AmbiSenseDiscovery:
    """Helper class to discover AmbiSense devices via mDNS."""

    @staticmethod
    async def discover_devices(hass: HomeAssistant) -> Dict[str, str]:
        """
        Discover AmbiSense devices using mDNS.
        
        Returns a dictionary of {name: host} for discovered devices.
        """
        discovered_devices = {}
        
        try:
            # Use HomeAssistant's zeroconf instance
            zc = await get_mdns(hass)
            
            # Look for services with '_ambisense._tcp.local.' type
            service_type = "_ambisense._tcp.local."
            
            # Perform a scan
            results = await zc.async_browse(service_type)
            
            for result in results:
                # Fetch service info
                info = await zc.async_get_service_info(result)
                
                if info:
                    # Extract hostname, removing trailing '.'
                    hostname = info.hostname.rstrip('.')
                    
                    # If there are addresses, use the first IPv4 address
                    if info.addresses:
                        # Prefer IPv4
                        ipv4_addresses = [addr for addr in info.addresses if ':' not in addr]
                        if ipv4_addresses:
                            ip_address = ipv4_addresses[0]
                            
                            # Use the service name as the device name
                            device_name = result.name or hostname
                            
                            discovered_devices[device_name] = ip_address
        
        except Exception as e:
            _LOGGER.error(f"Error during mDNS discovery: {e}")
        
        return discovered_devices


@config_entries.HANDLERS.register(DOMAIN)
class AmbiSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AmbiSense with mDNS support."""
    
    VERSION = 2  # Increment version for mDNS changes
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial user configuration step."""
        errors = {}
        
        # Try to discover devices first
        self._discovered_devices = await AmbiSenseDiscovery.discover_devices(self.hass)
        
        # If discovered devices exist, show discovery step
        if self._discovered_devices:
            return await self.async_step_device_selection()
        
        # Fallback to manual input if no devices discovered
        if user_input is not None:
            try:
                # Validate the manually entered host
                host = user_input.get(CONF_HOST, '').lower()
                
                # Check if host looks like a valid mDNS name
                if not host.endswith('.local'):
                    host += '.local'
                
                # Try to resolve mDNS name to IP if possible
                try:
                    ip_address = await self._resolve_mdns_to_ip(host)
                    user_input[CONF_HOST] = ip_address or host
                except Exception:
                    raise CannotConnect("Could not resolve mDNS name")
                
                info = await validate_input(self.hass, user_input)
                
                # Check if device with this host already exists
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device_selection(self, user_input=None):
        """Handle device selection step after discovery."""
        if user_input is not None:
            selected_device = user_input.get('device')
            if selected_device:
                # Get the IP for the selected device
                host = self._discovered_devices[selected_device]
                
                try:
                    info = await validate_input(self.hass, {
                        CONF_HOST: host, 
                        CONF_NAME: selected_device
                    })
                    
                    # Check if device with this host already exists
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

    async def _resolve_mdns_to_ip(self, mdns_name: str) -> Optional[str]:
        """
        Attempt to resolve an mDNS name to an IP address.
        
        This method uses zeroconf to resolve the mDNS name.
        Returns the IP address if successful, None otherwise.
        """
        try:
            zc = await get_mdns(self.hass)
            info = await zc.async_get_service_info("_http._tcp.local.", mdns_name)
            
            if info and info.addresses:
                # Prefer IPv4 addresses
                ipv4_addresses = [addr for addr in info.addresses if ':' not in addr]
                return ipv4_addresses[0] if ipv4_addresses else None
        except Exception as e:
            _LOGGER.error(f"mDNS resolution error: {e}")
        
        return None


async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]

    # Check if the device is reachable and responds correctly
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{host}/settings", timeout=10) as resp:
                if resp.status != 200:
                    raise CannotConnect(f"Error connecting to AmbiSense: {resp.status}")
                
                try:
                    await resp.json()
                except Exception as err:
                    raise CannotConnect(f"Error parsing response: {err}")

    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection error: {err}")
    except asyncio.TimeoutError:
        raise CannotConnect("Connection timed out")

    # Return info to be stored in the config entry
    return {"title": f"AmbiSense ({host})"}


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

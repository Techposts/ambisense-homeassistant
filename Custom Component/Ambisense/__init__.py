"""
AmbiSense integration for Home Assistant.
For more details about this integration, please refer to the documentation at
https://github.com/techposts/ambisense-homeassistant
https://claude.ai/chat/d71a8cba-eaf4-48cb-84ed-5d5ad6714b5f
"""
import asyncio
import logging
import aiohttp
import voluptuous as vol
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    UnitOfLength,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Define platform names
DOMAIN = "ambisense"
DEFAULT_NAME = "AmbiSense"
DATA_UPDATED = f"{DOMAIN}_data_updated"

PLATFORMS = ["light", "sensor", "number"]

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Scan interval (how often to poll the device)
SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the AmbiSense component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up AmbiSense from a config entry."""
    host = entry.data[CONF_HOST]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    coordinator = AmbiSenseDataUpdateCoordinator(hass, host, name)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class AmbiSenseDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AmbiSense data."""

    def __init__(self, hass, host, name):
        """Initialize."""
        self.host = host
        self.name = name
        self.data = {}
        self.available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from AmbiSense."""
        try:
            # Fetch both distance and settings
            distance = await self._fetch_distance()
            settings = await self._fetch_settings()
            
            # Combine the data
            data = {"distance": distance, **settings}
            return data
        except Exception as err:
            self.available = False
            _LOGGER.exception("Error communicating with AmbiSense: %s", err)
            raise

    async def _fetch_distance(self):
        """Fetch current distance from device."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.host}/distance", timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return int(text.strip())
                    else:
                        _LOGGER.error("Failed to get distance, status: %s", resp.status)
                        return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error fetching distance: %s", err)
            return None

    async def _fetch_settings(self):
        """Fetch settings from device."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.host}/settings", timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        _LOGGER.error("Failed to get settings, status: %s", resp.status)
                        return {}
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error fetching settings: %s", err)
            return {}
            
    async def async_update_settings(self, **kwargs):
        """Update settings on the device."""
        params = {}
        # Map from possible HA attributes to device parameters
        mapping = {
            "min_distance": "minDist",
            "max_distance": "maxDist",
            "brightness": "brightness",
            "light_span": "lightSpan",
            "rgb_color": None,  # Special handling for RGB
            "num_leds": "numLeds",
        }
        
        # Handle RGB specially
        if "rgb_color" in kwargs:
            r, g, b = kwargs["rgb_color"]
            params["redValue"] = r
            params["greenValue"] = g
            params["blueValue"] = b
        
        # Handle other parameters
        for key, value in kwargs.items():
            if key in mapping and mapping[key] is not None:
                params[mapping[key]] = value
        
        if not params:
            return False
            
        # Construct the URL with parameters
        url = f"http://{self.host}/set"
        param_strings = [f"{k}={v}" for k, v in params.items()]
        url += "?" + "&".join(param_strings)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    success = resp.status == 200
                    if success:
                        # Force an immediate data refresh
                        await self.async_refresh()
                    return success
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error updating settings: %s", err)
            return False
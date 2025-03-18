"""
AmbiSense integration for Home Assistant.
For more details about this integration, please refer to the documentation at
https://github.com/techposts/ambisense-homeassistant
"""
import asyncio
import logging
import aiohttp
import voluptuous as vol
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Define platform names
DOMAIN = "ambisense"
DEFAULT_NAME = "AmbiSense"
DATA_UPDATED = f"{DOMAIN}_data_updated"

# Add select and switch platforms
PLATFORMS = ["light", "sensor", "number", "select", "switch"]

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
    
    # Register services
    from .service import async_setup_services
    await async_setup_services(hass)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up AmbiSense from a config entry."""
    host = entry.data[CONF_HOST]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    coordinator = AmbiSenseDataUpdateCoordinator(hass, host, name)
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise ConfigEntryNotReady(f"Failed to connect to AmbiSense at {host}")

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # If this is the last entry, unload services
        if not hass.data[DOMAIN]:
            from .service import async_unload_services
            await async_unload_services(hass)
            
    return unload_ok

class AmbiSenseDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AmbiSense data."""

    def __init__(self, hass, host, name):
        """Initialize."""
        self.host = host
        self.name = name
        self.session = async_get_clientsession(hass)
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
        
        if settings is None and distance is None:
            self.available = False
            raise UpdateFailed("Failed to update data from AmbiSense device")
        
        # Use previous settings data if new fetch failed
        if settings is None and hasattr(self, "data") and "minDistance" in self.data:
            settings = {
                k: v for k, v in self.data.items() 
                if k != "distance"
            }
        
        # Combine the data (with defaults for missing values)
        data = {
            "distance": distance if distance is not None else 0,
            "minDistance": settings.get("minDistance", 30),
            "maxDistance": settings.get("maxDistance", 300),
            "brightness": settings.get("brightness", 255),
            "movingLightSpan": settings.get("movingLightSpan", 40),
            "numLeds": settings.get("numLeds", 300),
            "redValue": settings.get("redValue", 255),
            "greenValue": settings.get("greenValue", 255),
            "blueValue": settings.get("blueValue", 255),
            # Add any other parameters that are returned from the settings API
            # Using get() with defaults in case they're not in the API response
            "backgroundMode": settings.get("backgroundMode", False),
            "directionalLight": settings.get("directionalLight", True),
            "centerShift": settings.get("centerShift", 0),
            "trailLength": settings.get("trailLength", 5),
            "effectSpeed": settings.get("effectSpeed", 50),
            "effectIntensity": settings.get("effectIntensity", 100),
            "lightMode": settings.get("lightMode", "moving"), # Default to moving mode
        }
        
        self.available = True
        return data
    except Exception as err:
        self.available = False
        _LOGGER.exception("Error communicating with AmbiSense: %s", err)
        raise UpdateFailed(f"Error communicating with AmbiSense: {err}")

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
        # Add mappings for new parameters
        "background_mode": "backgroundMode",
        "directional_light": "directionalLight",
        "center_shift": "centerShift",
        "trail_length": "trailLength",
        "effect_speed": "effectSpeed",
        "effect_intensity": "effectIntensity",
        "light_mode": "lightMode",
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
            # Handle boolean parameters correctly for the API
            if isinstance(value, bool):
                value = 1 if value else 0
            params[mapping[key]] = value
    
    if not params:
        return False
        
    # Construct the URL with parameters
    url = f"http://{self.host}/set"
    param_strings = [f"{k}={v}" for k, v in params.items()]
    url += "?" + "&".join(param_strings)
    
    try:
        async with self.session.get(url, timeout=5) as resp:
            success = resp.status == 200
            if success:
                # Force an immediate data refresh
                await self.async_refresh()
            return success
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        _LOGGER.error("Error updating settings: %s", err)
        return False

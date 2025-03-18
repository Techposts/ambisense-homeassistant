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
    PERCENTAGE,
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

    async def _fetch_distance(self):
        """Fetch current distance from device."""
        try:
            async with self.session.get(f"http://{self.host}/distance", timeout=5) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    try:
                        return int(text.strip())
                    except ValueError:
                        _LOGGER.error("Invalid distance value: %s", text)
                        return None
                else:
                    _LOGGER.error("Failed to get distance, status: %s", resp.status)
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Error fetching distance: %s", err)
            return None

    async def _fetch_settings(self):
        """Fetch settings from device."""
        try:
            async with self.session.get(f"http://{self.host}/settings", timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.error("Failed to get settings, status: %s", resp.status)
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Error fetching settings: %s", err)
            return None
        except ValueError as err:
            _LOGGER.error("Error parsing settings JSON: %s", err)
            return None
                    
    # Add this to the `__init__.py` file in the AmbiSenseDataUpdateCoordinator class:
    
    async def async_update_settings(self, **kwargs):
        """Update device settings with improved response handling."""
        _LOGGER.debug(f"Received settings update request: {kwargs}")
        
        # Comprehensive parameter mapping
        param_map = {
            'min_distance': 'minDist',
            'max_distance': 'maxDist',
            'brightness': 'brightness',
            'light_span': 'lightSpan',
            'num_leds': 'numLeds',
            'center_shift': 'centerShift',
            'trail_length': 'trailLength',
            'effect_speed': 'effectSpeed',
            'effect_intensity': 'effectIntensity',
            'background_mode': 'backgroundMode',
            'directional_light': 'directionalLight',
            'light_mode': 'lightMode',
            'rgb_color': None  # Special handling for RGB
        }
        
        # Prepare parameters for API
        params = {}
        
        # Special handling for RGB color
        if 'rgb_color' in kwargs:
            r, g, b = kwargs['rgb_color']
            params['redValue'] = r
            params['greenValue'] = g
            params['blueValue'] = b
        
        # Process other parameters
        for ha_param, device_param in param_map.items():
            if ha_param in kwargs and device_param is not None:
                value = kwargs[ha_param]
                
                # Convert boolean to 1/0 for certain parameters
                if isinstance(value, bool):
                    value = 1 if value else 0
                
                params[device_param] = value
        
        _LOGGER.debug(f"Mapped parameters for API: {params}")
        
        # Construct URL with parameters
        if not params:
            _LOGGER.warning("No valid parameters to update")
            return False
        
        # Explicitly log directional light changes
        if 'directionalLight' in params:
            _LOGGER.info(f"Setting directionalLight={params['directionalLight']}")
    
        # Construct query string
        param_strings = [f"{k}={v}" for k, v in params.items()]
        url = f"http://{self.host}/set?{('&'.join(param_strings))}"
        
        _LOGGER.debug(f"Sending update request to: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Device response: {response_text}")
                    
                    # Try to parse JSON response
                    try:
                        response_data = await resp.json()
                        # Update our local data with the response data if available
                        if 'settings' in response_data:
                            # Map each setting back to our data structure
                            settings_data = response_data['settings']
                            if 'directionalLight' in settings_data:
                                self.data['directionalLight'] = settings_data['directionalLight'] == True or settings_data['directionalLight'] == "true"
                                _LOGGER.debug(f"Updated directionalLight from response: {self.data['directionalLight']}")
                            
                            # Trigger immediate data refresh
                            await self.async_refresh()
                            return True
                        
                    except ValueError:
                        # If JSON parsing fails, just rely on our refresh
                        pass
                    
                    # Immediate refresh to get updated state
                    await self.async_refresh()
                    return True
                else:
                    _LOGGER.error(f"Failed to update settings. Status: {resp.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating settings: {err}")
            return False

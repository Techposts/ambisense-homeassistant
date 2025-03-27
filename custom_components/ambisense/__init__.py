"""
AmbiSense integration for Home Assistant.
For more details about this integration, please refer to the documentation at
https://github.com/techposts/ambisense-homeassistant
"""
import asyncio
import logging
import aiohttp
import json
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

from .motion_handler import MotionSmoothingHandler
from .effect_handler import EffectParameterHandler

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
        
        # Initialize handlers for specialized endpoints
        self.motion_handler = MotionSmoothingHandler(host, self.session)
        self.effect_handler = EffectParameterHandler(host, self.session)

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
                "directionLightEnabled": settings.get("directionLightEnabled", False),
                "directionalLight": settings.get("directionLightEnabled", False),  # Alias for HA compatibility
                "centerShift": settings.get("centerShift", 0),
                "trailLength": settings.get("trailLength", 5),
                "effectSpeed": settings.get("effectSpeed", 50),
                "effectIntensity": settings.get("effectIntensity", 100),
                "lightMode": settings.get("lightMode", 0),
                
                # New Motion Smoothing Parameters
                "motionSmoothingEnabled": settings.get("motionSmoothingEnabled", False),
                "positionSmoothingFactor": settings.get("positionSmoothingFactor", 0.2),
                "velocitySmoothingFactor": settings.get("velocitySmoothingFactor", 0.1),
                "predictionFactor": settings.get("predictionFactor", 0.5),
                "positionPGain": settings.get("positionPGain", 0.1),
                "positionIGain": settings.get("positionIGain", 0.01),
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
                    json_text = await resp.text()
                    # Debug the raw JSON
                    _LOGGER.debug(f"Raw settings: {json_text}")
                    
                    # Parse the JSON with error handling
                    try:
                        settings = json.loads(json_text)
                        
                        # Map directionLightEnabled to directionalLight for consistency
                        if "directionLightEnabled" in settings and "directionalLight" not in settings:
                            settings["directionalLight"] = settings["directionLightEnabled"]
                        
                        return settings
                    except json.JSONDecodeError as err:
                        _LOGGER.error(f"Error parsing settings JSON: {err}")
                        return None
                else:
                    _LOGGER.error("Failed to get settings, status: %s", resp.status)
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Error fetching settings: %s", err)
            return None
                    
    async def async_update_settings(self, **kwargs):
        """Update device settings with improved response handling."""
        _LOGGER.debug(f"Received settings update request: {kwargs}")
        
        # Initialize successful flag
        success = True
        
        # Special handling for motion smoothing
        if 'motion_smoothing' in kwargs:
            motion_success = await self.motion_handler.set_motion_smoothing_enabled(
                kwargs.pop('motion_smoothing')
            )
            success = success and motion_success
        
        # Handle motion smoothing parameters
        for param in ['position_smoothing_factor', 'velocity_smoothing_factor', 
                     'prediction_factor', 'position_p_gain', 'position_i_gain']:
            if param in kwargs:
                value = kwargs.pop(param)
                param_success = await self.motion_handler.set_motion_smoothing_param(param, value)
                success = success and param_success
        
        # Handle effect parameters
        if 'effect_speed' in kwargs:
            speed_success = await self.effect_handler.set_effect_speed(
                kwargs.pop('effect_speed')
            )
            success = success and speed_success
            
        if 'effect_intensity' in kwargs:
            intensity_success = await self.effect_handler.set_effect_intensity(
                kwargs.pop('effect_intensity')
            )
            success = success and intensity_success
        
        # Handle light mode
        if 'light_mode' in kwargs:
            mode_success = await self.effect_handler.set_light_mode(
                kwargs.pop('light_mode')
            )
            success = success and mode_success
        
        # Map parameter names from HA to firmware format
        param_mapping = {
            'min_distance': 'minDist',
            'max_distance': 'maxDist',
            'light_span': 'lightSpan',
            'num_leds': 'numLeds',
            'center_shift': 'centerShift',
            'trail_length': 'trailLength',
            'background_mode': 'backgroundMode',
            'directional_light': 'directionLight',
            'rgb_color': None,  # Special handling for RGB
        }
        
        # Transform parameters to the names expected by the firmware
        firmware_params = {}
        for key, value in kwargs.items():
            # Special handling for RGB color
            if key == 'rgb_color' and isinstance(value, list) and len(value) == 3:
                firmware_params['redValue'] = value[0]
                firmware_params['greenValue'] = value[1]
                firmware_params['blueValue'] = value[2]
                continue
                
            # Use the mapped parameter name if available
            firmware_key = param_mapping.get(key, key)
            if firmware_key:
                firmware_params[firmware_key] = value
        
        # Handle any remaining parameters with standard API
        if firmware_params:
            # Special handling for boolean values
            for key, value in list(firmware_params.items()):
                if isinstance(value, bool):
                    firmware_params[key] = "true" if value else "false"
                    
            # Construct URL with parameters
            param_strings = [f"{k}={v}" for k, v in firmware_params.items()]
            url = f"http://{self.host}/set?{('&'.join(param_strings))}"
            
            _LOGGER.debug(f"Sending update request to: {url}")
            
            try:
                async with self.session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        response_text = await resp.text()
                        _LOGGER.debug(f"Device response: {response_text}")
                    else:
                        _LOGGER.error(f"Failed to update settings. Status: {resp.status}, Response: {await resp.text()}")
                        success = False
            except Exception as err:
                _LOGGER.error(f"Error updating settings: {err}")
                success = False
        
        # Trigger a refresh after settings changes
        await self.async_refresh()
        return success

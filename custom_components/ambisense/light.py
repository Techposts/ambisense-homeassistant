"""AmbiSense light platform."""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN, AmbiSenseDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up AmbiSense light from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AmbiSenseLightEntity(coordinator)])


class AmbiSenseLightEntity(CoordinatorEntity, LightEntity):
    """Representation of an AmbiSense light."""

    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_has_entity_name = True

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the light."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_light"
        self._attr_name = "LED Strip"
        self._is_on = True  # Default to on as there's no explicit on/off in AmbiSense
        
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="4.0.3",  # Updated to match firmware version
        )

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        # Check if brightness is 0 (considered off)
        if self.coordinator.data and self.coordinator.data.get("brightness", 0) == 0:
            return False
        return self._is_on

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("brightness", 255)

    @property
    def rgb_color(self):
        """Return the rgb color value [int, int, int]."""
        if not self.coordinator.data:
            return None
        
        red = self.coordinator.data.get("redValue", 255)
        green = self.coordinator.data.get("greenValue", 255)
        blue = self.coordinator.data.get("blueValue", 255)
        
        return (red, green, blue)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        self._is_on = True
        
        # Prepare settings to update
        settings = {}
        
        if ATTR_BRIGHTNESS in kwargs:
            settings["brightness"] = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug(f"Setting brightness to {kwargs[ATTR_BRIGHTNESS]}")
            
        if ATTR_RGB_COLOR in kwargs:
            # Instead of using rgb_color parameter, break it down into individual components
            # This matches how the firmware expects to receive color values
            r, g, b = kwargs[ATTR_RGB_COLOR]
            
            # Use direct firmware parameter names
            settings["redValue"] = r
            settings["greenValue"] = g
            settings["blueValue"] = b
            _LOGGER.debug(f"Setting RGB color to: R={r}, G={g}, B={b}")
        
        if settings:
            # Send the parameters directly with their firmware names
            firmware_params = {}
            
            # Map parameters to firmware names
            if "brightness" in settings:
                firmware_params["brightness"] = settings["brightness"]
            
            # RGB values are already using firmware names
            if "redValue" in settings:
                firmware_params["redValue"] = settings["redValue"]
                firmware_params["greenValue"] = settings["greenValue"]
                firmware_params["blueValue"] = settings["blueValue"]
            
            # Construct URL with parameters
            param_strings = [f"{k}={v}" for k, v in firmware_params.items()]
            url = f"http://{self.coordinator.host}/set?{('&'.join(param_strings))}"
            
            _LOGGER.debug(f"Light update URL: {url}")
            
            try:
                session = self.coordinator.session
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        response_text = await resp.text()
                        _LOGGER.debug(f"Device response for light update: {response_text}")
                    else:
                        _LOGGER.error(f"Failed to update light. Status: {resp.status}")
            except Exception as err:
                _LOGGER.error(f"Error updating light: {err}")
            
            # Force a refresh to get updated state
            await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the light off (by setting brightness to 0)."""
        self._is_on = False
        
        # Use direct firmware parameter
        url = f"http://{self.coordinator.host}/set?brightness=0"
        
        _LOGGER.debug(f"Light off URL: {url}")
        
        try:
            session = self.coordinator.session
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Device response for light off: {response_text}")
                else:
                    _LOGGER.error(f"Failed to turn off light. Status: {resp.status}")
        except Exception as err:
            _LOGGER.error(f"Error turning off light: {err}")
        
        # Force a refresh to get updated state
        await self.coordinator.async_refresh()

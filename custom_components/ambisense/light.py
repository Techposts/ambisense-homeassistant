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

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the light."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.name} Light"
        self._attr_unique_id = f"{coordinator.host}_light"
        self._is_on = True  # Default to on as there's no explicit on/off in AmbiSense

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
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
            
        if ATTR_RGB_COLOR in kwargs:
            settings["rgb_color"] = kwargs[ATTR_RGB_COLOR]
            
        if settings:
            await self.coordinator.async_update_settings(**settings)

    async def async_turn_off(self, **kwargs):
        """Turn the light off (by setting brightness to 0)."""
        self._is_on = False
        await self.coordinator.async_update_settings(brightness=0)
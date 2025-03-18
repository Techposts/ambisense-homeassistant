"""AmbiSense button platform."""
import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up AmbiSense button from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AmbiSenseApplySettingsButton(coordinator)])


class AmbiSenseApplySettingsButton(CoordinatorEntity, ButtonEntity):
    """Representation of an AmbiSense Apply Settings button."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_apply_settings"
        self._attr_name = "Apply Settings"
        self._attr_icon = "mdi:content-save-settings"
        
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="1.0",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        if not self.coordinator.data:
            return

        # Get all current settings from the coordinator's data
        settings = {
            "min_distance": self.coordinator.data.get("minDistance", 30),
            "max_distance": self.coordinator.data.get("maxDistance", 300),
            "brightness": self.coordinator.data.get("brightness", 255),
            "light_span": self.coordinator.data.get("movingLightSpan", 40),
            "rgb_color": [
                self.coordinator.data.get("redValue", 255),
                self.coordinator.data.get("greenValue", 255),
                self.coordinator.data.get("blueValue", 255)
            ],
            "num_leds": self.coordinator.data.get("numLeds", 300),
            "center_shift": self.coordinator.data.get("centerShift", 0),
            "trail_length": self.coordinator.data.get("trailLength", 5),
            "effect_speed": self.coordinator.data.get("effectSpeed", 50),
            "effect_intensity": self.coordinator.data.get("effectIntensity", 100),
            "background_mode": self.coordinator.data.get("backgroundMode", False),
            "directional_light": self.coordinator.data.get("directionalLight", True),
            "light_mode": self.coordinator.data.get("lightMode", "moving"),
        }
        
        # Send all settings at once to the device
        await self.coordinator.async_update_settings(**settings)

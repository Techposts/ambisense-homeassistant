"""AmbiSense select platform for light mode selection."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN, AmbiSenseDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Updated mapping between numeric modes and descriptive names based on firmware
MODE_MAP = {
    0: "Standard",
    1: "Rainbow",
    2: "Color Wave", 
    3: "Breathing", 
    4: "Solid",
    5: "Comet Trail",
    6: "Pulse Waves",
    7: "Fire Effect",
    8: "Theater Chase",
    9: "Dual Scan",
    10: "Motion Particles"
}

# Create reverse mapping for lookup
REVERSE_MODE_MAP = {v: k for k, v in MODE_MAP.items()}

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
):
    """Set up AmbiSense select entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        AmbiSenseLightModeSelect(coordinator),
    ]
    
    async_add_entities(entities)

class AmbiSenseLightModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of an AmbiSense light mode selection."""

    _attr_has_entity_name = True
    _attr_options = list(REVERSE_MODE_MAP.keys())
    _attr_icon = "mdi:lightbulb-variant"

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_light_mode"
        self._attr_name = "Light Mode"
        
        # Device info for device registry with updated version
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="4.0.3",  # Updated to match firmware version
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (self.coordinator.data is not None and 
                "lightMode" in self.coordinator.data)

    @property
    def current_option(self):
        """Return the current selected option."""
        if not self.coordinator.data:
            return None
        
        # Get numeric mode from coordinator data, default to 0 (Standard)
        current_mode = self.coordinator.data.get("lightMode", 0)
        
        # Convert numeric mode to descriptive name
        return MODE_MAP.get(current_mode, "Standard")

    async def async_select_option(self, option: str):
        """Change the selected option."""
        # Convert descriptive name back to numeric mode
        mode_value = REVERSE_MODE_MAP.get(option, 0)
        
        # Log the mode change for debugging
        _LOGGER.info(f"Changing light mode to {option} (numeric value: {mode_value})")
        
        # Update settings via coordinator
        await self.coordinator.async_update_settings(light_mode=mode_value)

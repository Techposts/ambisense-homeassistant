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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
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
    _attr_options = ["moving", "static", "effect"]
    _attr_icon = "mdi:lightbulb-variant"

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_light_mode"
        self._attr_name = "Light Mode"
        
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and "lightMode" in self.coordinator.data

    @property
    def current_option(self):
        """Return the current selected option."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("lightMode", "moving")

    async def async_select_option(self, option: str):
        """Change the selected option."""
        await self.coordinator.async_update_settings(light_mode=option)

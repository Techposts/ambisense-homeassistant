"""AmbiSense switch platform for boolean settings."""
import logging

from homeassistant.components.switch import SwitchEntity
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
    """Set up AmbiSense switch entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        AmbiSenseBackgroundModeSwitch(coordinator),
        AmbiSenseDirectionalLightSwitch(coordinator),
    ]
    
    async_add_entities(entities)

class AmbiSenseSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base class for AmbiSense switch entities."""

    _attr_has_entity_name = True

    def __init__(
        self, 
        coordinator: AmbiSenseDataUpdateCoordinator,
        name_suffix: str,
        key: str,
        icon: str = None
    ):
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._attr_name = name_suffix
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._key = key
        if icon:
            self._attr_icon = icon
            
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="3.1",
        )

class AmbiSenseDirectionalLightSwitch(AmbiSenseSwitchEntity):
    """Representation of the directional light switch."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Directional Light",
            key="directionalLight",
            icon="mdi:arrow-right-thick"
        )

    @property
    def is_on(self) -> bool:
        """Explicitly control the on/off state from coordinator data."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available for directional light")
            return False
        
        # Use explicit boolean conversion and logging
        current_state = bool(self.coordinator.data.get('directionalLight', False))
        _LOGGER.debug(f"Current Directional Light state: {current_state}")
        return current_state

    async def async_turn_on(self, **kwargs):
        """Turn on the directional light with comprehensive logging."""
        _LOGGER.debug("Attempting to turn ON Directional Light")
        
        # Force a specific state with explicit logging
        try:
            result = await self.coordinator.async_update_settings(directional_light=True)
            _LOGGER.info(f"Directional Light ON request result: {result}")
            
            # Force a refresh to ensure state synchronization
            await self.coordinator.async_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning on Directional Light: {e}")

    async def async_turn_off(self, **kwargs):
        """Turn off the directional light with comprehensive logging."""
        _LOGGER.debug("Attempting to turn OFF Directional Light")
        
        # Force a specific state with explicit logging
        try:
            result = await self.coordinator.async_update_settings(directional_light=False)
            _LOGGER.info(f"Directional Light OFF request result: {result}")
            
            # Force a refresh to ensure state synchronization
            await self.coordinator.async_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning off Directional Light: {e}")

class AmbiSenseBackgroundModeSwitch(AmbiSenseSwitchEntity):
    """Representation of the background mode switch."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Background Mode",
            key="backgroundMode",
            icon="mdi:lightbulb-group"
        )

"""AmbiSense switch platform for boolean settings."""
import logging
import asyncio

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
        self._is_on = False  # Local state tracking
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

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and self._key in self.coordinator.data

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if not self.coordinator.data:
            return False
        # Update local state from coordinator
        self._is_on = bool(self.coordinator.data.get(self._key, False))
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        param_mapping = {
            "backgroundMode": "background_mode",
            "directionalLight": "directional_light",
        }
        param_name = param_mapping.get(self._key, self._key)
        await self.coordinator.async_update_settings(**{param_name: True})
        # Optimistically update state
        self._is_on = True
        self.async_write_ha_state()
        # Force refresh after a delay to get confirmed state
        await asyncio.sleep(1)  
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        param_mapping = {
            "backgroundMode": "background_mode",
            "directionalLight": "directional_light",
        }
        param_name = param_mapping.get(self._key, self._key)
        await self.coordinator.async_update_settings(**{param_name: False})
        # Optimistically update state 
        self._is_on = False
        self.async_write_ha_state()
        # Force refresh after a delay to get confirmed state
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()

class AmbiSenseDirectionalLightSwitch(AmbiSenseSwitchEntity):
    """Representation of the directional light switch."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Directional Light",
            key="directionLight",
            icon="mdi:arrow-right-thick"
        )
        # We'll add specific handling for this switch
        self._attr_entity_registry_enabled_default = True

    async def async_turn_on(self, **kwargs):
        """Turn on directional light with enhanced handling."""
        _LOGGER.debug("Turning ON Directional Light")
        success = await self.coordinator.async_update_settings(directional_light=True)
        _LOGGER.info(f"Directional Light ON request result: {success}")
        
        # Set state optimistically
        self._is_on = True
        self.async_write_ha_state()
        
        # Force a refresh after a delay to confirm state
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()
        
        # Debug log the state after refresh
        _LOGGER.debug(f"After refresh, directional light state: {self.coordinator.data.get('directionalLight', 'unknown')}")

    async def async_turn_off(self, **kwargs):
        """Turn off directional light with enhanced handling."""
        _LOGGER.debug("Turning OFF Directional Light")
        success = await self.coordinator.async_update_settings(directional_light=False)
        _LOGGER.info(f"Directional Light OFF request result: {success}")
        
        # Set state optimistically
        self._is_on = False
        self.async_write_ha_state()
        
        # Force a refresh after a delay to confirm state
        await asyncio.sleep(1)
        await self.coordinator.async_refresh()
        
        # Debug log the state after refresh
        _LOGGER.debug(f"After refresh, directional light state: {self.coordinator.data.get('directionalLight', 'unknown')}")

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

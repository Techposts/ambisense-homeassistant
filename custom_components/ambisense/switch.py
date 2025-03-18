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
            sw_version="1.0",
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
        return bool(self.coordinator.data.get(self._key, False))

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        param_mapping = {
            "backgroundMode": "background_mode",
            "directionalLight": "directional_light",
        }
        param_name = param_mapping.get(self._key, self._key)
        await self.coordinator.async_update_settings(**{param_name: True})

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        param_mapping = {
            "backgroundMode": "background_mode",
            "directionalLight": "directional_light",
        }
        param_name = param_mapping.get(self._key, self._key)
        await self.coordinator.async_update_settings(**{param_name: False})


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

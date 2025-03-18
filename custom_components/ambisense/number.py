"""AmbiSense number platform for configurable settings."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfLength
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
    """Set up AmbiSense number entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        AmbiSenseMinDistanceNumber(coordinator),
        AmbiSenseMaxDistanceNumber(coordinator),
        AmbiSenseLightSpanNumber(coordinator),
        AmbiSenseNumLedsNumber(coordinator),
        # Add these new number entities
        AmbiSenseCenterShiftNumber(coordinator),
        AmbiSenseTrailLengthNumber(coordinator),
        AmbiSenseEffectSpeedNumber(coordinator),
        AmbiSenseEffectIntensityNumber(coordinator),
    ]
    
    async_add_entities(entities)

# Add these new number entity classes

class AmbiSenseCenterShiftNumber(AmbiSenseNumberEntity):
    """Representation of the center shift setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Center Shift",
            key="centerShift",
            minimum=-100,
            maximum=100,
            step=1,
            icon="mdi:arrow-expand-horizontal"
        )


class AmbiSenseTrailLengthNumber(AmbiSenseNumberEntity):
    """Representation of the trail length setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Trail Length",
            key="trailLength",
            minimum=0,
            maximum=100,
            step=1,
            icon="mdi:blur-linear"
        )


class AmbiSenseEffectSpeedNumber(AmbiSenseNumberEntity):
    """Representation of the effect speed setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Effect Speed",
            key="effectSpeed",
            minimum=1,
            maximum=100,
            step=1,
            unit=PERCENTAGE,
            icon="mdi:speedometer"
        )


class AmbiSenseEffectIntensityNumber(AmbiSenseNumberEntity):
    """Representation of the effect intensity setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Effect Intensity",
            key="effectIntensity",
            minimum=1,
            maximum=100,
            step=1,
            unit=PERCENTAGE,
            icon="mdi:brightness-6"
        )


class AmbiSenseNumberEntity(CoordinatorEntity, NumberEntity):
    """Base class for AmbiSense number entities."""

    _attr_has_entity_name = True

    def __init__(
        self, 
        coordinator: AmbiSenseDataUpdateCoordinator,
        name_suffix: str,
        key: str,
        minimum: float,
        maximum: float,
        step: float,
        unit: str = None
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_name = name_suffix
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._key = key
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        if unit:
            self._attr_native_unit_of_measurement = unit
            
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.name,
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and self._key in self.coordinator.data

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value):
        """Set new value."""
        # Convert from coordinator key to API parameter name
        param_mapping = {
            "minDistance": "min_distance",
            "maxDistance": "max_distance",
            "movingLightSpan": "light_span",
            "numLeds": "num_leds",
        }
        
        param_name = param_mapping.get(self._key, self._key)
        await self.coordinator.async_update_settings(**{param_name: int(value)})


class AmbiSenseMinDistanceNumber(AmbiSenseNumberEntity):
    """Representation of the minimum distance setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Minimum Distance",
            key="minDistance",
            minimum=0,
            maximum=200,
            step=1,
            unit=UnitOfLength.CENTIMETERS,
        )


class AmbiSenseMaxDistanceNumber(AmbiSenseNumberEntity):
    """Representation of the maximum distance setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Maximum Distance",
            key="maxDistance",
            minimum=50,
            maximum=500,
            step=1,
            unit=UnitOfLength.CENTIMETERS,
        )


class AmbiSenseLightSpanNumber(AmbiSenseNumberEntity):
    """Representation of the light span setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Light Span",
            key="movingLightSpan",
            minimum=1,
            maximum=100,
            step=1,
        )


class AmbiSenseNumLedsNumber(AmbiSenseNumberEntity):
    """Representation of the number of LEDs setting."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Number of LEDs",
            key="numLeds",
            minimum=1,
            maximum=2000,
            step=1,
        )

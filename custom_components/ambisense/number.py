"""AmbiSense number platform for configurable settings."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfLength, PERCENTAGE
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
        AmbiSenseCenterShiftNumber(coordinator),
        AmbiSenseTrailLengthNumber(coordinator),
        AmbiSenseEffectSpeedNumber(coordinator),
        AmbiSenseEffectIntensityNumber(coordinator),
        
        # New Motion Smoothing Entities
        AmbiSensePositionSmoothingNumber(coordinator),
        AmbiSenseVelocitySmoothingNumber(coordinator),
        AmbiSensePredictionFactorNumber(coordinator),
        AmbiSensePositionPGainNumber(coordinator),
        AmbiSensePositionIGainNumber(coordinator),
    ]
    
    async_add_entities(entities)


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
        unit: str = None,
        icon: str = None,
        attribute_map: dict = None
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_name = name_suffix
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._key = key
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attribute_map = attribute_map or {}
        if unit:
            self._attr_native_unit_of_measurement = unit
        if icon:
            self._attr_icon = icon
            
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="AmbiSense",
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="3.5",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and any(key in self.coordinator.data for key in self._attribute_map.get('alt_keys', [self._key]))

    @property
    def native_value(self):
        """Return the current value."""
        if not self.coordinator.data:
            return None

        # Look for the value in multiple possible keys
        for key in self._attribute_map.get('alt_keys', [self._key]):
            value = self.coordinator.data.get(key)
            if value is not None:
                # Apply any conversion if specified
                converter = self._attribute_map.get('converter')
                return converter(value) if converter else value
        return None

    async def async_set_native_value(self, value):
        """Set new value."""
        # Get the service parameter name and handle conversion
        param_name = self._attribute_map.get('param_name', self._key)
        service_param = self._attribute_map.get('service_param', param_name)
        
        # Optional pre-conversion
        if 'pre_converter' in self._attribute_map:
            value = self._attribute_map['pre_converter'](value)
        
        await self.coordinator.async_update_settings(**{service_param: value})


# All existing entities keep their original implementation
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
            icon="mdi:ruler",
            attribute_map={
                'alt_keys': ['minDistance'],
                'service_param': 'min_distance'
            }
        )


# Existing implementations... (keep previous code)

# NEW MOTION SMOOTHING ENTITIES
class AmbiSensePositionSmoothingNumber(AmbiSenseNumberEntity):
    """Representation of the position smoothing factor."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Position Smoothing Factor",
            key="positionSmoothingFactor",
            minimum=0,
            maximum=1,
            step=0.01,
            icon="mdi:blur",
            attribute_map={
                'alt_keys': ['positionSmoothingFactor'],
                'service_param': 'positionSmoothingFactor',
                'pre_converter': lambda x: round(x, 2)  # Ensure 2 decimal precision
            }
        )


class AmbiSenseVelocitySmoothingNumber(AmbiSenseNumberEntity):
    """Representation of the velocity smoothing factor."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Velocity Smoothing Factor",
            key="velocitySmoothingFactor",
            minimum=0,
            maximum=1,
            step=0.01,
            icon="mdi:speedometer",
            attribute_map={
                'alt_keys': ['velocitySmoothingFactor'],
                'service_param': 'velocitySmoothingFactor',
                'pre_converter': lambda x: round(x, 2)  # Ensure 2 decimal precision
            }
        )


class AmbiSensePredictionFactorNumber(AmbiSenseNumberEntity):
    """Representation of the prediction factor."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Prediction Factor",
            key="predictionFactor",
            minimum=0,
            maximum=1,
            step=0.01,
            icon="mdi:chart-line-variant",
            attribute_map={
                'alt_keys': ['predictionFactor'],
                'service_param': 'predictionFactor',
                'pre_converter': lambda x: round(x, 2)  # Ensure 2 decimal precision
            }
        )


class AmbiSensePositionPGainNumber(AmbiSenseNumberEntity):
    """Representation of the position proportional gain."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Position P Gain",
            key="positionPGain",
            minimum=0,
            maximum=1,
            step=0.01,
            icon="mdi:play-speed",
            attribute_map={
                'alt_keys': ['positionPGain'],
                'service_param': 'positionPGain',
                'pre_converter': lambda x: round(x, 2)  # Ensure 2 decimal precision
            }
        )


class AmbiSensePositionIGainNumber(AmbiSenseNumberEntity):
    """Representation of the position integral gain."""

    def __init__(self, coordinator):
        """Initialize the entity."""
        super().__init__(
            coordinator=coordinator,
            name_suffix="Position I Gain",
            key="positionIGain",
            minimum=0,
            maximum=0.1,
            step=0.001,
            icon="mdi:sine-wave",
            attribute_map={
                'alt_keys': ['positionIGain'],
                'service_param': 'positionIGain',
                'pre_converter': lambda x: round(x, 3)  # Ensure 3 decimal precision
            }
        )

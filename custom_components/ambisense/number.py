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
            sw_version="4.0.3",  # Updated version
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
        
        # Log the parameter update
        _LOGGER.debug(f"Setting {service_param} to {value} (entity: {self._attr_name})")
        
        # Special direct handling for certain parameters
        if service_param == 'center_shift':
            # Use the effect handler for center shift
            if hasattr(self.coordinator, 'effect_handler'):
                await self.coordinator.effect_handler.set_center_shift(value)
                await self.coordinator.async_refresh()
                return
        elif service_param == 'trail_length':
            # Use the effect handler for trail length
            if hasattr(self.coordinator, 'effect_handler'):
                await self.coordinator.effect_handler.set_trail_length(value)
                await self.coordinator.async_refresh()
                return
        
        # Standard parameter update
        await self.coordinator.async_update_settings(**{service_param: value})


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
                'service_param': 'min_distance',
                'firmware_param': 'minDist'  # Added for reference
            }
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
            icon="mdi:ruler",
            attribute_map={
                'alt_keys': ['maxDistance'],
                'service_param': 'max_distance',
                'firmware_param': 'maxDist'  # Added for reference
            }
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
            icon="mdi:led-strip-variant",
            attribute_map={
                'alt_keys': ['movingLightSpan'],
                'service_param': 'light_span',
                'firmware_param': 'lightSpan'  # Added for reference
            }
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
            icon="mdi:led-strip",
            attribute_map={
                'alt_keys': ['numLeds'],
                'service_param': 'num_leds',
                'firmware_param': 'numLeds'  # Added for reference
            }
        )


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
            icon="mdi:arrow-expand-horizontal",
            attribute_map={
                'alt_keys': ['centerShift'],
                'service_param': 'center_shift',
                'firmware_param': 'centerShift'  # Added for reference
            }
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
            icon="mdi:blur-linear",
            attribute_map={
                'alt_keys': ['trailLength'],
                'service_param': 'trail_length',
                'firmware_param': 'trailLength'  # Added for reference
            }
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
            icon="mdi:speedometer",
            attribute_map={
                'alt_keys': ['effectSpeed'],
                'service_param': 'effect_speed',
                'firmware_param': 'effectSpeed'  # Added for reference
            }
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
            icon="mdi:brightness-6",
            attribute_map={
                'alt_keys': ['effectIntensity'],
                'service_param': 'effect_intensity',
                'firmware_param': 'effectIntensity'  # Added for reference
            }
        )


# MOTION SMOOTHING ENTITIES
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
                'service_param': 'position_smoothing_factor',
                'firmware_param': 'positionSmoothingFactor',  # Added for reference
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
                'service_param': 'velocity_smoothing_factor',
                'firmware_param': 'velocitySmoothingFactor',  # Added for reference
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
                'service_param': 'prediction_factor',
                'firmware_param': 'predictionFactor',  # Added for reference
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
                'service_param': 'position_p_gain',
                'firmware_param': 'positionPGain',  # Added for reference
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
                'service_param': 'position_i_gain',
                'firmware_param': 'positionIGain',  # Added for reference
                'pre_converter': lambda x: round(x, 3)  # Ensure 3 decimal precision
            }
        )

"""AmbiSense services."""
import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

from . import DOMAIN, AmbiSenseDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_UPDATE_SETTINGS = "update_settings"

# Parameter constants
ATTR_MIN_DISTANCE = "min_distance"
ATTR_MAX_DISTANCE = "max_distance"
ATTR_BRIGHTNESS = "brightness"
ATTR_LIGHT_SPAN = "light_span"
ATTR_RGB_COLOR = "rgb_color"
ATTR_NUM_LEDS = "num_leds"
ATTR_CENTER_SHIFT = "center_shift"
ATTR_TRAIL_LENGTH = "trail_length"
ATTR_EFFECT_SPEED = "effect_speed"
ATTR_EFFECT_INTENSITY = "effect_intensity"
ATTR_BACKGROUND_MODE = "background_mode"
ATTR_DIRECTIONAL_LIGHT = "directional_light"
ATTR_LIGHT_MODE = "light_mode"

# New Motion Smoothing Parameters
ATTR_MOTION_SMOOTHING = "motion_smoothing"
ATTR_POSITION_SMOOTHING_FACTOR = "position_smoothing_factor"
ATTR_VELOCITY_SMOOTHING_FACTOR = "velocity_smoothing_factor"
ATTR_PREDICTION_FACTOR = "prediction_factor"
ATTR_POSITION_P_GAIN = "position_p_gain"
ATTR_POSITION_I_GAIN = "position_i_gain"

# Schema for the update_settings service
UPDATE_SETTINGS_SCHEMA = vol.Schema(
    {
        # Original parameters
        vol.Optional(ATTR_MIN_DISTANCE): vol.All(vol.Coerce(int), vol.Range(min=0, max=200)),
        vol.Optional(ATTR_MAX_DISTANCE): vol.All(vol.Coerce(int), vol.Range(min=50, max=500)),
        vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        vol.Optional(ATTR_LIGHT_SPAN): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional(ATTR_RGB_COLOR): vol.All(
            vol.Length(3), [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))]
        ),
        vol.Optional(ATTR_NUM_LEDS): vol.All(vol.Coerce(int), vol.Range(min=1, max=2000)),
        
        # New parameters
        vol.Optional(ATTR_CENTER_SHIFT): vol.All(vol.Coerce(int), vol.Range(min=-100, max=100)),
        vol.Optional(ATTR_TRAIL_LENGTH): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional(ATTR_EFFECT_SPEED): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional(ATTR_EFFECT_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional(ATTR_BACKGROUND_MODE): cv.boolean,
        vol.Optional(ATTR_DIRECTIONAL_LIGHT): cv.boolean,
        vol.Optional(ATTR_LIGHT_MODE): vol.In(["moving", "static", "effect"]),
        
        # Motion Smoothing Parameters
        vol.Optional(ATTR_MOTION_SMOOTHING): cv.boolean,
        vol.Optional(ATTR_POSITION_SMOOTHING_FACTOR): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional(ATTR_VELOCITY_SMOOTHING_FACTOR): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional(ATTR_PREDICTION_FACTOR): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional(ATTR_POSITION_P_GAIN): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional(ATTR_POSITION_I_GAIN): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=0.1)
        ),
    }
)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the AmbiSense integration."""
    
    async def async_update_settings_service(service_call: ServiceCall) -> None:
        """Handle update settings service calls."""
        entity_ids = service_call.data.get("entity_id")
        
        if not entity_ids:
            return
            
        # Get entities and ensure they are AmbiSense entities
        component = hass.data.get(LIGHT_DOMAIN)
        if not component:
            return
            
        target_entities = []
        for entity_id in entity_ids:
            entity = component.get_entity(entity_id)
            if entity and hasattr(entity, 'coordinator') and isinstance(entity.coordinator, AmbiSenseDataUpdateCoordinator):
                target_entities.append(entity)
        
        if not target_entities:
            _LOGGER.warning("No valid AmbiSense entities found for service call")
            return
            
        # Extract settings
        settings = {}
        # Original settings
        if ATTR_MIN_DISTANCE in service_call.data:
            settings["min_distance"] = service_call.data[ATTR_MIN_DISTANCE]
        if ATTR_MAX_DISTANCE in service_call.data:
            settings["max_distance"] = service_call.data[ATTR_MAX_DISTANCE]
        if ATTR_BRIGHTNESS in service_call.data:
            settings["brightness"] = service_call.data[ATTR_BRIGHTNESS]
        if ATTR_LIGHT_SPAN in service_call.data:
            settings["light_span"] = service_call.data[ATTR_LIGHT_SPAN]
        if ATTR_RGB_COLOR in service_call.data:
            settings["rgb_color"] = service_call.data[ATTR_RGB_COLOR]
        if ATTR_NUM_LEDS in service_call.data:
            settings["num_leds"] = service_call.data[ATTR_NUM_LEDS]
        
        # Extended settings
        if ATTR_CENTER_SHIFT in service_call.data:
            settings["center_shift"] = service_call.data[ATTR_CENTER_SHIFT]
        if ATTR_TRAIL_LENGTH in service_call.data:
            settings["trail_length"] = service_call.data[ATTR_TRAIL_LENGTH]
        if ATTR_EFFECT_SPEED in service_call.data:
            settings["effect_speed"] = service_call.data[ATTR_EFFECT_SPEED]
        if ATTR_EFFECT_INTENSITY in service_call.data:
            settings["effect_intensity"] = service_call.data[ATTR_EFFECT_INTENSITY]
        
        # Boolean settings
        if ATTR_BACKGROUND_MODE in service_call.data:
            settings["background_mode"] = service_call.data[ATTR_BACKGROUND_MODE]
        if ATTR_DIRECTIONAL_LIGHT in service_call.data:
            settings["directional_light"] = service_call.data[ATTR_DIRECTIONAL_LIGHT]
        if ATTR_LIGHT_MODE in service_call.data:
            settings["light_mode"] = service_call.data[ATTR_LIGHT_MODE]
        
        # Motion Smoothing Parameters
        if ATTR_MOTION_SMOOTHING in service_call.data:
            settings["motion_smoothing"] = service_call.data[ATTR_MOTION_SMOOTHING]
        if ATTR_POSITION_SMOOTHING_FACTOR in service_call.data:
            settings["position_smoothing_factor"] = service_call.data[ATTR_POSITION_SMOOTHING_FACTOR]
        if ATTR_VELOCITY_SMOOTHING_FACTOR in service_call.data:
            settings["velocity_smoothing_factor"] = service_call.data[ATTR_VELOCITY_SMOOTHING_FACTOR]
        if ATTR_PREDICTION_FACTOR in service_call.data:
            settings["prediction_factor"] = service_call.data[ATTR_PREDICTION_FACTOR]
        if ATTR_POSITION_P_GAIN in service_call.data:
            settings["position_p_gain"] = service_call.data[ATTR_POSITION_P_GAIN]
        if ATTR_POSITION_I_GAIN in service_call.data:
            settings["position_i_gain"] = service_call.data[ATTR_POSITION_I_GAIN]
            
        # Apply settings to all target devices
        for entity in target_entities:
            await entity.coordinator.async_update_settings(**settings)

    async def async_apply_settings_service(service_call: ServiceCall) -> None:
        """Handle apply settings service calls."""
        entity_ids = service_call.data.get("entity_id")
        
        if not entity_ids:
            return
            
        # Get entities and ensure they are AmbiSense entities
        component = hass.data.get(LIGHT_DOMAIN)
        if not component:
            return
            
        target_entities = []
        for entity_id in entity_ids:
            entity = component.get_entity(entity_id)
            if entity and hasattr(entity, 'coordinator') and isinstance(entity.coordinator, AmbiSenseDataUpdateCoordinator):
                target_entities.append(entity)
        
        if not target_entities:
            _LOGGER.warning("No valid AmbiSense entities found for service call")
            return
            
        # For each entity, send all current settings to force a refresh/update
        for entity in target_entities:
            coordinator = entity.coordinator
            if coordinator.data:
                # Get all current settings from the coordinator's data
                settings = {
                    "min_distance": coordinator.data.get("minDistance", 30),
                    "max_distance": coordinator.data.get("maxDistance", 300),
                    "brightness": coordinator.data.get("brightness", 255),
                    "light_span": coordinator.data.get("movingLightSpan", 40),
                    "rgb_color": [
                        coordinator.data.get("redValue", 255),
                        coordinator.data.get("greenValue", 255),
                        coordinator.data.get("blueValue", 255)
                    ],
                    "num_leds": coordinator.data.get("numLeds", 300),
                    "center_shift": coordinator.data.get("centerShift", 0),
                    "trail_length": coordinator.data.get("trailLength", 5),
                    "effect_speed": coordinator.data.get("effectSpeed", 50),
                    "effect_intensity": coordinator.data.get("effectIntensity", 100),
                    "background_mode": coordinator.data.get("backgroundMode", False),
                    "directional_light": coordinator.data.get("directionalLight", True),
                    "light_mode": coordinator.data.get("lightMode", "moving"),
                    
                    # Motion Smoothing Parameters
                    "motion_smoothing": coordinator.data.get("motionSmoothingEnabled", False),
                    "position_smoothing_factor": coordinator.data.get("positionSmoothingFactor", 0.2),
                    "velocity_smoothing_factor": coordinator.data.get("velocitySmoothingFactor", 0.1),
                    "prediction_factor": coordinator.data.get("predictionFactor", 0.5),
                    "position_p_gain": coordinator.data.get("positionPGain", 0.1),
                    "position_i_gain": coordinator.data.get("positionIGain", 0.01),
                }
                
                # Send all settings at once to force a complete update
                await coordinator.async_update_settings(**settings)
                _LOGGER.info(f"Applied all settings to {entity.entity_id}")

    
    # Register our service with Home Assistant
    # Register the apply_settings service
    hass.services.async_register(
        DOMAIN,
        "apply_settings",
        async_apply_settings_service,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
    )
    

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload AmbiSense services."""
    if hass.services.has_service(DOMAIN, SERVICE_UPDATE_SETTINGS):
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SETTINGS)

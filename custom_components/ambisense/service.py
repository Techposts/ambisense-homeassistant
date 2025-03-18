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

    # Add these new parameter constants
    ATTR_CENTER_SHIFT = "center_shift"
    ATTR_TRAIL_LENGTH = "trail_length"
    ATTR_EFFECT_SPEED = "effect_speed"
    ATTR_EFFECT_INTENSITY = "effect_intensity"
    ATTR_BACKGROUND_MODE = "background_mode"
    ATTR_DIRECTIONAL_LIGHT = "directional_light"
    ATTR_LIGHT_MODE = "light_mode"
    
    # Update the schema to include new parameters
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
        }
    )
    
    # Update the service call handler to process new parameters
    async def async_update_settings_service(service_call: ServiceCall) -> None:
        """Handle update settings service calls."""
    
        
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
         if ATTR_CENTER_SHIFT in service_call.data:
        settings["center_shift"] = service_call.data[ATTR_CENTER_SHIFT]
        if ATTR_TRAIL_LENGTH in service_call.data:
            settings["trail_length"] = service_call.data[ATTR_TRAIL_LENGTH]
        if ATTR_EFFECT_SPEED in service_call.data:
            settings["effect_speed"] = service_call.data[ATTR_EFFECT_SPEED]
        if ATTR_EFFECT_INTENSITY in service_call.data:
            settings["effect_intensity"] = service_call.data[ATTR_EFFECT_INTENSITY]
        if ATTR_BACKGROUND_MODE in service_call.data:
            settings["background_mode"] = service_call.data[ATTR_BACKGROUND_MODE]
        if ATTR_DIRECTIONAL_LIGHT in service_call.data:
            settings["directional_light"] = service_call.data[ATTR_DIRECTIONAL_LIGHT]
        if ATTR_LIGHT_MODE in service_call.data:
            settings["light_mode"] = service_call.data[ATTR_LIGHT_MODE]    
        # Apply settings to all target devices
        for entity in target_entities:
            await entity.coordinator.async_update_settings(**settings)
    
    # Register our service with Home Assistant
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_SETTINGS,
        async_update_settings_service,
        schema=UPDATE_SETTINGS_SCHEMA,
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload AmbiSense services."""
    if hass.services.has_service(DOMAIN, SERVICE_UPDATE_SETTINGS):
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SETTINGS)

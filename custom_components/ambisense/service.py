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

ATTR_MIN_DISTANCE = "min_distance"
ATTR_MAX_DISTANCE = "max_distance"
ATTR_BRIGHTNESS = "brightness"
ATTR_LIGHT_SPAN = "light_span"
ATTR_RGB_COLOR = "rgb_color"
ATTR_NUM_LEDS = "num_leds"

UPDATE_SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_MIN_DISTANCE): vol.All(vol.Coerce(int), vol.Range(min=0, max=200)),
        vol.Optional(ATTR_MAX_DISTANCE): vol.All(vol.Coerce(int), vol.Range(min=50, max=500)),
        vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        vol.Optional(ATTR_LIGHT_SPAN): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional(ATTR_RGB_COLOR): vol.All(
            vol.Length(3), [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))]
        ),
        vol.Optional(ATTR_NUM_LEDS): vol.All(vol.Coerce(int), vol.Range(min=1, max=2000)),
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

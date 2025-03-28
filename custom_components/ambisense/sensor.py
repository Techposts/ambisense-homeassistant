"""AmbiSense sensor platform for distance reading."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    """Set up AmbiSense sensor from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AmbiSenseDistanceSensor(coordinator)])


class AmbiSenseDistanceSensor(CoordinatorEntity, SensorEntity):
    """Representation of an AmbiSense Distance Sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_has_entity_name = True

    def __init__(self, coordinator: AmbiSenseDataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_distance"
        self._attr_name = "Distance"
        
        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=coordinator.name,
            manufacturer="TechPosts Media",
            model="AmbiSense Radar-Controlled LED System",
            sw_version="4.0.3",  # Updated to match firmware version
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and "distance" in self.coordinator.data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None or "distance" not in self.coordinator.data:
            return None
        return self.coordinator.data["distance"]

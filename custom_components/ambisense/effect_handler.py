"""Enhanced effect parameter handler for AmbiSense integration."""
import logging
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)

class EffectParameterHandler:
    """Class to handle effect parameters."""
    
    def __init__(self, host, session):
        """Initialize the handler."""
        self.host = host
        self.session = session
        
    async def set_effect_speed(self, value: int) -> bool:
        """Set effect speed parameter."""
        url = f"http://{self.host}/setEffectSpeed?value={value}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.debug(f"Successfully updated effect speed to {value}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update effect speed. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating effect speed: {err}")
            return False
            
    async def set_effect_intensity(self, value: int) -> bool:
        """Set effect intensity parameter."""
        url = f"http://{self.host}/setEffectIntensity?value={value}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.debug(f"Successfully updated effect intensity to {value}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update effect intensity. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating effect intensity: {err}")
            return False
            
    async def set_light_mode(self, mode) -> bool:
        """Set light mode parameter."""
        # If it's a string mode name, it needs to be converted to numeric value
        if isinstance(mode, str):
            from .select import REVERSE_MODE_MAP
            if mode in REVERSE_MODE_MAP:
                mode = REVERSE_MODE_MAP[mode]
            else:
                _LOGGER.error(f"Unknown light mode: {mode}")
                return False
                
        url = f"http://{self.host}/setLightMode?mode={mode}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.debug(f"Successfully updated light mode to {mode}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update light mode. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating light mode: {err}")
            return False

"""Enhanced effect parameter handler for AmbiSense integration."""
import logging
import aiohttp
import asyncio
import json

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
        
        _LOGGER.debug(f"Setting effect speed: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Effect speed response: {response_text}")
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
        
        _LOGGER.debug(f"Setting effect intensity: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Effect intensity response: {response_text}")
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
        
        _LOGGER.debug(f"Setting light mode: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Successfully updated light mode to {mode}. Response: {response_text}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update light mode. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating light mode: {err}")
            return False
            
    async def set_directional_light(self, enabled: bool) -> bool:
        """Enable or disable directional light."""
        enabled_str = "true" if enabled else "false"
        url = f"http://{self.host}/setDirectionalLight?enabled={enabled_str}"
        
        _LOGGER.debug(f"Setting directional light: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Successfully set directional light to {enabled}. Response: {response_text}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update directional light. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating directional light: {err}")
            return False
            
    async def set_background_mode(self, enabled: bool) -> bool:
        """Enable or disable background mode."""
        enabled_str = "true" if enabled else "false"
        url = f"http://{self.host}/setBackgroundMode?enabled={enabled_str}"
        
        _LOGGER.debug(f"Setting background mode: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Successfully set background mode to {enabled}. Response: {response_text}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update background mode. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating background mode: {err}")
            return False
            
    async def set_center_shift(self, value: int) -> bool:
        """Set center shift parameter."""
        url = f"http://{self.host}/setCenterShift?value={value}"
        
        _LOGGER.debug(f"Setting center shift: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Successfully set center shift to {value}. Response: {response_text}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update center shift. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating center shift: {err}")
            return False
            
    async def set_trail_length(self, value: int) -> bool:
        """Set trail length parameter."""
        url = f"http://{self.host}/setTrailLength?value={value}"
        
        _LOGGER.debug(f"Setting trail length: {url}")
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    _LOGGER.debug(f"Successfully set trail length to {value}. Response: {response_text}")
                    return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update trail length. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating trail length: {err}")
            return False

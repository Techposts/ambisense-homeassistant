"""Motion smoothing parameter handler for AmbiSense integration."""
import logging
import aiohttp
import asyncio
import json

_LOGGER = logging.getLogger(__name__)

class MotionSmoothingHandler:
    """Class to handle motion smoothing parameters."""
    
    def __init__(self, host, session):
        """Initialize the handler."""
        self.host = host
        self.session = session
        
    async def set_motion_smoothing_enabled(self, enabled: bool) -> bool:
        """Enable or disable motion smoothing."""
        enabled_str = "true" if enabled else "false"
        url = f"http://{self.host}/setMotionSmoothing?enabled={enabled_str}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.debug(f"Successfully {'enabled' if enabled else 'disabled'} motion smoothing")
                    return True
                else:
                    _LOGGER.error(f"Failed to update motion smoothing. Status: {resp.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating motion smoothing: {err}")
            return False
            
    async def set_motion_smoothing_param(self, param_name: str, value: float) -> bool:
        """Set a specific motion smoothing parameter."""
        # Map from Home Assistant parameter names to firmware parameter names
        param_map = {
            "position_smoothing_factor": "positionSmoothingFactor",
            "velocity_smoothing_factor": "velocitySmoothingFactor",
            "prediction_factor": "predictionFactor",
            "position_p_gain": "positionPGain",
            "position_i_gain": "positionIGain"
        }
        
        # Get the firmware parameter name
        device_param = param_map.get(param_name)
        if not device_param:
            _LOGGER.error(f"Unknown motion smoothing parameter: {param_name}")
            return False
            
        # Format value based on parameter type (different parameters need different precision)
        if param_name == "position_i_gain":
            formatted_value = f"{value:.3f}"  # 3 decimal places for I gain
        else:
            formatted_value = f"{value:.2f}"  # 2 decimal places for other parameters
            
        url = f"http://{self.host}/setMotionSmoothingParam?param={device_param}&value={formatted_value}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    try:
                        response_data = await resp.json()
                        if response_data.get("status") == "success":
                            _LOGGER.debug(f"Successfully updated {device_param} to {formatted_value}")
                            return True
                        else:
                            _LOGGER.warning(f"Device returned non-success status for {device_param}: {response_data}")
                            return False
                    except json.JSONDecodeError:
                        # If not valid JSON, just check status code
                        _LOGGER.debug(f"Successfully updated {device_param} to {formatted_value} (non-JSON response)")
                        return True
                else:
                    response_text = await resp.text()
                    _LOGGER.error(f"Failed to update {device_param}. Status: {resp.status}, Response: {response_text}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error updating {device_param}: {err}")
            return False

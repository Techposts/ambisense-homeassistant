# AmbiSense Home Assistant Integration

This custom component integrates your AmbiSense radar-controlled LED system with Home Assistant.

## Features

- **Distance Sensor**: Monitor real-time distance readings from the radar sensor
- **LED Control**: Adjust brightness, color, and other parameters of your LED strip
- **Configuration**: Set minimum and maximum distance thresholds, light span, and number of LEDs

## Installation

### HACS (Home Assistant Community Store)

1. Ensure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations > ⋮ > Custom repositories
3. Add this repository URL with category "Integration"
4. Click "Install" on the AmbiSense integration
5. Restart Home Assistant

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/ambisense` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Setup via UI (Recommended)

1. Go to **Configuration** → **Devices & Services**
2. Click the "+ Add Integration" button in the bottom-right corner
3. Search for "AmbiSense" and select it
4. Enter the IP address of your AmbiSense device (default: 192.168.4.1)
5. Enter a name for your device (optional)
6. Click "Submit"

### Configuration Variables

- **host** (Required): The IP address of your AmbiSense device
- **name** (Optional): A friendly name for your device

## Entities

After setting up the integration, you'll have access to the following entities:

### Sensor
- **Distance Sensor**: Shows the current distance detected by the radar sensor in centimeters

### Light
- **LED Light**: Control the LED strip brightness and color

### Number
- **Minimum Distance**: Set the minimum detection distance
- **Maximum Distance**: Set the maximum detection distance
- **Light Span**: Adjust the number of LEDs lit in the moving light effect
- **Number of LEDs**: Configure the total number of LEDs in your strip

## Automation Ideas

Here are some ways you can use this integration in your Home Assistant automations:

1. **Presence Detection**: Use the distance sensor to trigger automations when someone enters a room
2. **Dynamic Lighting**: Adjust other lights in your home based on the radar readings
3. **Energy Saving**: Turn off lights when no movement is detected for a period of time

## Troubleshooting

- Ensure your AmbiSense device is powered on and connected to your network
- Check that you can access the web interface at `http://[IP_ADDRESS]`
- Verify that the firmware on your AmbiSense device is up to date
- Check the Home Assistant logs for any error messages related to the AmbiSense integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

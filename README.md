# AmbiSense Home Assistant Integration

This custom component integrates your AmbiSense radar-controlled LED system with Home Assistant, allowing you to monitor and control your ambient lighting based on proximity detection.

## Features

- **Automatic Discovery**: Finds your AmbiSense devices on your network using mDNS
- **Distance Sensor**: Monitor real-time distance readings from the radar sensor
- **LED Control**: Adjust brightness, color, and other parameters of your LED strip
- **Configuration**: Set minimum and maximum distance thresholds, light span, and number of LEDs
- **Device Registry**: All entities are properly grouped under a single device in Home Assistant

## Prerequisites

- Home Assistant installed and running (version 2023.3.0 or later)
- AmbiSense device connected to your network
- The device should have an IP address that is reachable from your Home Assistant instance

## Installation

### HACS (Home Assistant Community Store) - Recommended

1. Ensure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations > ⋮ > Custom repositories
3. Add this repository URL with category "Integration"
4. Click "Install" on the AmbiSense integration
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/ambisense` directory into your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Automatic Discovery (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click the "+ Add Integration" button in the bottom-right corner
3. Search for "AmbiSense" and select it
4. If your AmbiSense device is on the network, it should be discovered automatically
5. Follow the prompts to complete the setup

### Manual Configuration

If automatic discovery doesn't find your device:

1. Go to **Settings** → **Devices & Services**
2. Click the "+ Add Integration" button
3. Search for "AmbiSense" and select it
4. Enter the IP address of your AmbiSense device (default: 192.168.4.1)
5. Enter a name for your device (optional)
6. Click "Submit"

## Entities

After setting up the integration, you'll have access to the following entities:

### Sensor
- **Distance Sensor**: Shows the current distance detected by the radar sensor in centimeters

### Light
- **LED Light**: Control the LED strip with on/off, brightness, and RGB color

### Number
- **Minimum Distance**: Set the minimum detection distance (cm)
- **Maximum Distance**: Set the maximum detection distance (cm)
- **Light Span**: Adjust the number of LEDs lit in the moving light effect
- **Number of LEDs**: Configure the total number of LEDs in your strip

## Automation Examples

Here are some examples of how you can use this integration in your Home Assistant automations:

### Turn on room lights when someone enters

```yaml
automation:
  - alias: "Turn on lights when someone enters"
    trigger:
      platform: numeric_state
      entity_id: sensor.ambisense_distance
      below: 100
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
```

### Change LED color based on time of day

```yaml
automation:
  - alias: "Evening LED color"
    trigger:
      platform: time
      at: "20:00:00"
    action:
      service: light.turn_on
      target:
        entity_id: light.ambisense_light
      data:
        rgb_color: [255, 160, 80]
        brightness: 180
```

### Energy Saving Mode

```yaml
automation:
  - alias: "Energy saving - no presence detected"
    trigger:
      platform: numeric_state
      entity_id: sensor.ambisense_distance
      above: 400
      for: 
        minutes: 10
    action:
      service: light.turn_off
      target:
        entity_id: light.ambisense_light
```

## Troubleshooting

### Device Not Discovered

- Ensure your AmbiSense device is powered on and connected to your network
- Check that mDNS (Bonjour/Avahi) is working on your network
- You can try manual configuration with the IP address instead

### Cannot Connect to Device

- Verify you can access the web interface directly at `http://<IP_ADDRESS>/`
- Check if your firewall is blocking connections to the device
- Ensure the ESP32 is connected to your network and has a static IP
- Try restarting both the AmbiSense device and Home Assistant

### Entities Show as Unavailable

- Check the Home Assistant logs for any error messages related to the AmbiSense integration
- Verify the device is still powered on and connected to the network
- Try updating the integration or reinstalling it

### Radar Sensor Not Working

- Make sure the LD2410 sensor is properly connected to the ESP32
- Check the physical connections and cables
- Verify the sensor is not obstructed or placed behind materials that block radar

### LED Control Not Working

- Check the physical connections between the ESP32 and the LED strip
- Verify the LED strip is powered properly
- Test the LED functionality using the web interface at `http://<IP_ADDRESS>/`

## Advanced Configuration

### Using mDNS Hostname

If your network supports mDNS (most do), you can use the hostname instead of IP:

1. The device hostname format is `ambisense-<location>.local`
2. For example: `ambisense-livingroom.local`

### Setting Up Static IP

For more reliable connectivity, set up a static IP for your AmbiSense device:

1. Access your router's DHCP settings
2. Find the MAC address of your AmbiSense device 
3. Assign a static IP to that MAC address

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Created by Ravi Singh (TechPosts Media)
- Home Assistant component developed by the AmbiSense community

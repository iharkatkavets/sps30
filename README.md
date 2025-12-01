# Sensirion SPS30

## Introduction

Python-based driver for [Sensirion SPS30](https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/) particulate matter sensor. Tested on Raspberry Pi Zero/Zero W/3B+/4B.

### Wiring

#### Sensor

```none
                                 Pin 1   Pin 5
                                   |       |
                                   V       V
.------------------------------------------------.
|                                .-----------.   |
|                                | x x x x x |   |
|                                '-----------'   |
|     []          []          []          []     |
'------------------------------------------------'
```

| Pin | Description                                       | UART | I2C |
| :-: | :------------------------------------------------ | ---- | --- |
|  1  | Supply voltage 5V                                 | VDD  | VDD |
|  2  | UART receiving pin/ I2C serial data input/ output | RX   | SDA |
|  3  | UART transmitting pin/ I2C serial clock input     | TX   | SCL |
|  4  | Interface select (UART: floating (NC) /I2C: GND)  | NC   | GND |
|  5  | Ground                                            | GND  | GND |

#### I2C Interface

```none
  Sensor Pins                                 Raspberry Pi Pins
.-------.-----.                             .----------.---------.
| Pin 1 | VDD |-----------------------------|    5V    | Pin 2/4 |
| Pin 2 | SDA |-----------------------------| I2C1 SDA |  Pin 3  |
| Pin 3 | SCL |-----------------------------| I2C1 SCL |  Pin 5  |
| Pin 4 | GND |-----.                       |          |         |
| Pin 5 | GND |-----'-----------------------|   GND    | Pin 6/9 |
'-------'-----'                             '----------'---------'
```

### Example

Default parameters of `SPS30` class

| Parameter | Value | Description             |
| --------- | ----- | ----------------------- |
| bus       | 1     | I2C bus of Raspberry Pi |
| address   | 0x69  | Default I2C address     |

```python
import sys
import json
from time import sleep
from sps30 import SPS30


if __name__ == "__main__":
    pm_sensor = SPS30()
    print(f"Firmware version: {pm_sensor.firmware_version()}")
    print(f"Product type: {pm_sensor.product_type()}")
    print(f"Serial number: {pm_sensor.serial_number()}")
    print(f"Status register: {pm_sensor.read_status_register()}")
    print(
        f"Auto cleaning interval: {pm_sensor.read_auto_cleaning_interval()}s")
    print(f"Set auto cleaning interval: {pm_sensor.write_auto_cleaning_interval_days(2)}s")
    pm_sensor.start_measurement()

    while True:
        try:
            print(json.dumps(pm_sensor.get_measurement(), indent=2))
            sleep(2)

        except KeyboardInterrupt:
            print("Stopping measurement...")
            pm_sensor.stop_measurement()
            sys.exit()
```

### Output data format

```json
{
  "measurements": [
    {
        "measurement": "mass_density",
        "parameter": "pm1.0",
        "value": 1.883,
        "unit": "ug/m3"
    },
    {
        "measurement": "mass_density",
        "parameter": "pm2.5",
        "value": 1.883,
        "unit": "ug/m3"
    },
    {
        "measurement": "mass_density",
        "parameter": "pm4.0",
        "value": 1.883,
        "unit": "ug/m3"
    },
    {
        "measurement": "mass_density",
        "parameter": "pm10",
        "value": 1.883,
        "unit": "ug/m3"
    },
    {
        "measurement": "particle_count",
        "parameter": "pm0.5",
        "value": 1.883,
        "unit": "#/cm3"
    },
    {
        "measurement": "particle_count",
        "parameter": "pm1.0",
        "value": 1.883,
        "unit": "#/cm3"
    },
    {
        "measurement": "particle_count",
        "parameter": "pm2.5",
        "value": 1.883,
        "unit": "#/cm3"
    },
    {
        "measurement": "particle_count",
        "parameter": "pm4.0",
        "value": 1.883,
        "unit": "#/cm3"
    },
    {
        "measurement": "particle_count",
        "parameter": "pm10",
        "value": 1.883,
        "unit": "#/cm3"
    },
    {
        "measurement": "particle_size",
        "value": 1.53,
        "unit": "um"
    }
  ],
  "timestamp": 1630217804,
  "sensor_id": "pizero1"
}
```

### Dependencies

None

### `systemd` service configuration

Create a file at `/etc/systemd/system/sps30-measurement.service`

```ini
[Unit]
Description=SPS30 Measurement service
After=network.target

[Service]
Environment="PYTHONPATH=/home/pi/services/sps30-service"
ExecStart=/usr/bin/python3 /home/pi/services/sps30-service/examples/sps30-service.py --host "raspberrypi:4001" --delay 1
WorkingDirectory=/home/pi/
User=root
Group=root
Restart=always
RestartSec=10
TimeoutStopSec=10
KillSignal=SIGTERM
StandardOutput=journal
StandardError=journal
StateDirectory=sps30-measurement
RuntimeDirectory=sps30-measurement

[Install]
WantedBy=multi-user.target
```

Then run 

```sh
sudo systemctl daemon-reload
sudo systemctl enable sps30-measurement
sudo systemctl start sps30-measurement
```

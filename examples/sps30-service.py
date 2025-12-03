#!/usr/bin/env python3

import sys
import json
import urllib.request
import urllib.error
from typing import Any
from datetime import datetime, timezone
from sps30 import SPS30
import argparse
import time
import signal
import logging


logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)


parser = argparse.ArgumentParser(description="SPS30 measument tool")
parser.add_argument("--host", type=str, required=True, help="The host of api backend, like: raspberrypi.local:4001")
parser.add_argument("--delay", default=10, type=int, required=False, help="Delay between measurements, default: 10")
parser.add_argument("--sensor", default="sps30", type=str, required=True, help="sensor name for a request")
parser.add_argument("--sensor_id", default=None, type=str, required=True, help="The sensor_id parameter for a request, like: sps30.pizerow")
opts = parser.parse_args()


logger = logging.getLogger("sps30")


def upload(host: str, payload: dict[str, Any], sensor_id: str):
    """Upload sensor data as JSON to the API endpoint."""

    url = f"http://{host}/api/measurements/{sensor_id}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
            url, 
            data=body, 
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
                },
            )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            logger.info("Upload succeeded: %d %s", response.status, response.reason)
    except urllib.error.HTTPError as e:
        logger.error(
            "HTTPError %d %s\nPayload:\n%s",
            e.code, e.reason,
            json.dumps(payload, ensure_ascii=False, indent=2)
        )
    except urllib.error.URLError as e:
        logger.error(f"URLError: {e.reason}")
    except Exception as e: 
        logger.exception(f"Unexpected error during upload: {e}")


def map_measurements_to_request(data: dict[str, Any], sensor: str) -> dict[str, Any]:
    sensor_data = data.get("sensor_data", {})

    result = {"sensor": sensor, "measurements": []}

    if "mass_concentration" in sensor_data and "mass_concentration_unit" in sensor_data:
        for param, value in sensor_data["mass_concentration"].items():
            result["measurements"].append({
                "measurement": "mass_concentration",
                "parameter": param,
                "value": value,
                "unit": sensor_data["mass_concentration_unit"]
            })

    if "number_concentration" in sensor_data and "number_concentration_unit" in sensor_data:
        for param, value in sensor_data["number_concentration"].items():
            result["measurements"].append({
                "measurement": "number_concentration",
                "parameter": param,
                "value": value,
                "unit": sensor_data["number_concentration_unit"]
            })

    if "typical_particle_size" in sensor_data and "typical_particle_size_unit" in sensor_data:
        result["measurements"].append({
            "measurement": "typical_particle_size",
            "value": sensor_data["typical_particle_size"],
            "unit": sensor_data["typical_particle_size_unit"]
        })

    return result


pm_sensor = SPS30()
def run(host, delay, sensor, sensor_id):
    res = pm_sensor.write_auto_cleaning_interval_days(2)
    if res["ok"]:
        logger.info(f"Set auto cleaning interval: {res['value']}s")
    else:
        logger.info(f"Failed to set auto cleaning interval: {res['error']}")

    pm_sensor.start_measurement()
    while True:
        try:
            measurements = pm_sensor.get_measurement()
            if not len(measurements):
                logger.info("Skip upload because of data absent")
                continue

            request_data = map_measurements_to_request(measurements, sensor)
            if not request_data:
                logger.info("Skip sending because of data absent")
                continue

            upload(host, request_data, sensor_id=sensor_id)
        except KeyboardInterrupt:
            logger.info("Exiting ...")
            cleanup()
            sys.exit(0)
        finally:
            time.sleep(delay)


def cleanup():
    logger.info("Stop SPS30 sensor hardware safely...")
    pm_sensor.stop_measurement()
    time.sleep(2)
    logger.info("Stop SPS30 sensor complete.")


def signal_handler(signum, _):
    logger.info(f"Received signal {signum}, stopping service...")
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)  # Handle systemd stop/restart
signal.signal(signal.SIGINT, signal_handler)   # Handle manual CTRL+C


def main():
    run(opts.host, opts.delay, opts.sensor, opts.sensor_id)


if __name__ == "__main__":
    main()

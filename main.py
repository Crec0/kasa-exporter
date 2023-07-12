import time

import schedule
from prometheus_client import Gauge, Counter, CollectorRegistry, start_http_server

from kasa.config import Config, PlugConfig
from kasa.kasa_smart_plug import KasaSmartPlug

REGISTRY = CollectorRegistry()

STATUS = Gauge("kasa_online", "Device online", ["plug_name"], registry=REGISTRY)
UPTIME = Gauge("kasa_uptime", "Time in seconds since online", ["plug_name"], registry=REGISTRY)
RSSI = Gauge("kasa_rssi", "Wifi signal strength indicator", ["plug_name"], registry=REGISTRY)
POWER = Gauge("kasa_power_total", "Power consumption since device connected in KWh", ["plug_name"], registry=REGISTRY)
LOAD = Gauge("kasa_power_load", "Current power in Watt", ["plug_name"], registry=REGISTRY)


def scrape_plug(plug_config: PlugConfig):
    plug = KasaSmartPlug(plug_config.addr, plug_config.email, plug_config.password)
    name = plug_config.name

    try:
        dev_info = plug.get_device_info()
    except Exception as e:
        STATUS.labels(name).set(0)
        print(f"Error collecting data for {plug_config.addr}")
        print(e)
        return

    STATUS.labels(name).set(1)
    UPTIME.labels(name).set(dev_info.on_time)
    RSSI.labels(name).set(dev_info.rssi)

    try:
        power_info = plug.get_realtime_energy_usage()
    except Exception as e:
        print(f"Error collecting energy data for {plug_config.addr}")
        print(e)
        return

    POWER.labels(name).set(power_info.power)
    LOAD.labels(name).set(power_info.load)


def scrape(plug_configs: list[PlugConfig]):
    for plug_config in plug_configs:
        schedule.every(plug_config.interval).seconds.do(scrape_plug, plug_config)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    config = Config.read_config("config.yml")
    start_http_server(config.prometheus_port, registry=REGISTRY)
    scrape(config.plugs)


if __name__ == '__main__':
    main()

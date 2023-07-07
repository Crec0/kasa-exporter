import time
from threading import Thread

import schedule
import uvicorn
from fastapi import FastAPI
from prometheus_client import Gauge, Counter, CollectorRegistry, make_asgi_app

from kasa.config import Config, PlugConfig
from kasa.kasa_smart_plug import KasaSmartPlug

REGISTRY = CollectorRegistry()
STATUS = Gauge("kasa_online", "Device online", ["name"], registry=REGISTRY)
RELAY_STATE = Gauge("kasa_relay_state", "Relay state (switch on/off)", ["name"], registry=REGISTRY)
UPTIME = Counter("kasa_uptime", "Time in seconds since online", ["name"], registry=REGISTRY)
WIFI_STRENGTH = Gauge("kasa_rssi", "Wifi signal strength indicator", ["name"], registry=REGISTRY)
POWER = Gauge("kasa_power_total", "Power consumption since device connected in KWh", ["name"], registry=REGISTRY)
LOAD = Gauge("kasa_power_load", "Current power in Watt", ["name"], registry=REGISTRY)


def scrape_plug(plug_config: PlugConfig):
    plug = KasaSmartPlug(plug_config.addr, plug_config.email, plug_config.password)
    name = plug_config.name

    try:
        dev_info = plug.get_device_info()
    except Exception as e:
        STATUS.labels(name=name).set(0)
        print(f"Error collecting data for {plug_config.addr}")
        print(e)
        return

    STATUS.labels(name=name).set(1)
    RELAY_STATE.labels(name=name).set(1 if dev_info.device_on else 0)
    UPTIME.labels(name=name).inc(dev_info.on_time)
    WIFI_STRENGTH.labels(name=name).set(dev_info.rssi)

    try:
        power_info = plug.get_realtime_energy_usage()
    except Exception as e:
        print(f"Error collecting energy data for {plug_config.addr}")
        print(e)
        return

    POWER.labels(name=name).set(power_info.power)
    LOAD.labels(name=name).set(power_info.load)


def scrape(plug_configs: list[PlugConfig]):
    for plug_config in plug_configs:
        schedule.every(plug_config.interval).seconds.do(scrape_plug, plug_config)

    while True:
        schedule.run_pending()
        time.sleep(1)


app = FastAPI(debug=True)
app.mount("/metrics", make_asgi_app(registry=REGISTRY))


def main():
    config = Config.read_config("config.yml")

    scrapper_thread = Thread(target=scrape, args=[config.plugs])
    scrapper_thread.daemon = True
    scrapper_thread.start()

    uvicorn.run("main:app", port=config.prometheus.port, log_level="debug")


if __name__ == '__main__':
    main()

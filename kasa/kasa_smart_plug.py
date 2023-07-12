import time

from kasa.auth import Auth
from kasa.schema import DeviceInfo, EnergyUsageInfo

ENERGY_DATA_INTERVALS = {
    'hourly': 60,
    'daily': 1440,
    'monthly': 43200
}


class KasaSmartPlug:
    def __init__(self, ip: str, email: str, password: str):
        self.__auth = Auth(ip)
        self.__auth.handshake()
        self.__auth.login(email, password)

    def get_device_info(self) -> DeviceInfo:
        request = self.__auth.send_request({
            "method": "get_device_info",
            "requestTimeMils": 0,
        })
        if request["error_code"] != 0:
            raise ValueError(f"Invalid response from the plug. {request}")
        return DeviceInfo(**request["result"])

    def get_realtime_energy_usage(self) -> EnergyUsageInfo:
        request = self.__auth.send_request({
            "method": "get_energy_usage",
            "requestTimeMils": 0,
        })
        if request["error_code"] != 0:
            raise ValueError(f"Invalid response from the plug. {request}")
        return EnergyUsageInfo(**request["result"])

    def get_overtime_energy_usage(self, start: int, end: int, interval: int) -> dict:
        return self.__auth.send_request({
            "method": "get_energy_data",
            "params": {"start_timestamp": start, "end_timestamp": end, "interval": interval},
            "requestTimeMils": round(time.time() * 1000),
        })

    def more_info(self) -> dict:
        """
        get_electricity_price_config
        get_current_power
        get_protection_power
        get_max_power
        get_led_info
        get_power_data # requires same params from energy data
        """
        return self.__auth.send_request({
            "method": "get_led_info",
            # "params": {
            #     "start_timestamp": round(time.time()) - 86400, "end_timestamp": round(time.time()), "interval": 60
            # },
            "requestTimeMils": round(time.time() * 1000),
        })

from base64 import b64decode

from pydantic import BaseModel


class DeviceInfo(BaseModel):
    auto_off_remain_time: int
    auto_off_status: str
    avatar: str
    default_states: dict[str, dict | str]
    device_id: str
    device_on: bool
    fw_id: str
    fw_ver: str
    has_set_location_info: bool
    hw_id: str
    hw_ver: str
    ip: str
    lang: str
    latitude: int
    longitude: int
    mac: str
    model: str
    nickname: str  # b64 encoded
    oem_id: str
    on_time: int
    overheated: bool
    power_protection_status: str
    region: str
    rssi: int
    signal_level: int
    specs: str
    ssid: str  # b64 encoded
    time_diff: int
    type: str

    @property
    def nickname_decoded(self) -> str:
        return b64decode(self.nickname).decode("UTF-8")

    @property
    def ssid_decoded(self) -> str:
        return b64decode(self.ssid).decode("UTF-8")


class EnergyUsageInfo(BaseModel):
    current_power: int
    electricity_charge: list[int]
    local_time: str
    month_energy: int
    month_runtime: int
    today_energy: int
    today_runtime: int

    @property
    def load(self) -> float:
        return self.current_power / 1000

    @property
    def power(self) -> float:
        return self.today_energy / 1000

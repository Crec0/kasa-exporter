from copy import deepcopy
from dataclasses import dataclass

import yaml
from pydantic import BaseModel, validator


class PrometheusConfig(BaseModel):
    port: int
    endpoint: str


class PlugConfig(BaseModel):
    name: str
    addr: str
    email: str = None
    password: str = None
    interval: int = 30

    @validator('email')
    def email_should_not_be_none(cls, _email):
        if _email is None:
            raise ValueError("Email is missing from both plug and common config. Please provide an email!")
        return _email

    @validator('password')
    def password_should_not_be_none(cls, _password):
        if _password is None:
            raise ValueError("Password is missing from both plug and common config. Please provide a password!")
        return _password

    @validator('interval')
    def is_interval_at_least_5_seconds(cls, _interval):
        if _interval < 5:
            raise ValueError("Interval is invalid. Please choose a positive number greater than 5")
        return _interval


@dataclass
class Config:
    prometheus: PrometheusConfig
    plugs: list[PlugConfig]

    @staticmethod
    def read_config(path: str) -> "Config":
        try:
            with open(path, "r") as config_file:
                data = yaml.load(config_file, yaml.Loader)
        except yaml.YAMLError | FileNotFoundError as e:
            print(e)
            exit(-1)

        # populate each plug config with defaults and globals
        populated_plugs = [
            PlugConfig(**(deepcopy(data['common'] | plug)))
            for plug in data['plugs']
        ]
        prometheus_config = PrometheusConfig(**data['prometheus'])

        return Config(prometheus_config, populated_plugs)

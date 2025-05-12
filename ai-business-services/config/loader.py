import os

import yaml
from dotenv import load_dotenv

load_dotenv()
service = os.getenv("service")
env = os.getenv("env")


def load_config():
    file_name = f"/configs/configs.dev.yaml"
    with open(file_name, "r") as stream:
        try:
            package_config = yaml.safe_load(stream)
            common_config, service_config = package_config.get(
                "common", {}
            ), package_config.get(service, {})
            cfg = {}
            cfg.update(common_config)
            cfg.update(service_config)
            return cfg
        except yaml.YAMLError as exc:
            print(exc)


cfg = load_config()

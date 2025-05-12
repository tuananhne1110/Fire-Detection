import os

import yaml
from dotenv import load_dotenv

load_dotenv()
env = os.getenv("RUN_ENV")


# Load config from file with RUN ENV dev or prod
def load_config():
    file_name = f"/app/configs/config.{env}.yaml"
    with open(file_name, "r") as stream:
        try:
            cfg = yaml.safe_load(stream)
            return cfg
        except yaml.YAMLError as exc:
            print(exc)


cfg = load_config()

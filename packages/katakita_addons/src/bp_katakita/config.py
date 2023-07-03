import os
import json

CONFIG_FILEPATH = os.environ.get("BP_KATAKITA_CONFIG_FILEPATH")

def load_config():
    if CONFIG_FILEPATH is None:
        raise Exception("BP_KATAKITA_CONFIG_FILEPATH environment variable not set")
    with open(CONFIG_FILEPATH) as f:
        config = json.load(f)
    return config
    
def load_secrets():
    config = load_config()
    with open(config["SECRETS_PATH"]) as f:
        secrets = json.load(f)
    return secrets
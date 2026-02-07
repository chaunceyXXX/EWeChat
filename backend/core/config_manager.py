import json
import os
from typing import Dict, Any

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "monitor_folder": "",
    "wecom": {
        "corpid": "",
        "secret": "",
        "agentid": "",
        "touser": "@all",  # UserID list separated by | or @all
        "toparty": ""
    },
    "schedule": {
        "enabled": False,
        "time": "09:00", # HH:MM
        "frequency": "daily" # daily, hourly
    }
}

class ConfigManager:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG)

    def load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG

    def save_config(self, config: Dict[str, Any]):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        config = self.load_config()
        return config.get(key, default)

    def update(self, key: str, value: Any):
        config = self.load_config()
        config[key] = value
        self.save_config(config)

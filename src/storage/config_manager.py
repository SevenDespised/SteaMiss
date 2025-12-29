import json
import os
import logging


logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path="config/settings.json"):
        self.config_path = config_path
        self.settings = {
            "explorer_paths": ["C:/", "C:/", "C:/"],
            "steam_api_key": "",
            "steam_id": "",
            "steam_alt_ids": [],
            "timer_reminder": {},
            "timer_reminder_presets": [],
            "llm_api_key": "",
            "llm_base_url": "",
            "llm_model": ""
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                logger.exception("Error loading config: %s", self.config_path)

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception("Error saving config: %s", self.config_path)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_config()

    def update_dict(self, settings_dict):
        """批量更新配置"""
        self.settings.update(settings_dict)
        self.save_config()

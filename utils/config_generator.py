from pathlib import Path
from typing import TYPE_CHECKING
import yaml

if TYPE_CHECKING:
    from ..organs import SystemConfig

class ConfigGenerator:
    """配置文件生成器, 通过依赖注入调整config"""
    def __init__(self, work_path: Path, instance: "SystemConfig"):
        self._work_path = work_path
        self._instance = instance

    def generate_config(self):
        """生成配置文件，如果文件已存在则不覆盖"""
        config_path = self._work_path / f"{self._instance.__class__.__name__}.yaml"
        if config_path.exists():
            return
        config = {}
        for attr in self._instance.attr_order:
            config[attr] = getattr(self._instance, attr)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    def reload_config(self):
        config_path = self._work_path / f"{self._instance.__class__.__name__}.yaml"
        if not config_path.exists():
            return
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not config:
                return
            for key, value in config.items():
                if hasattr(self._instance, key):
                    setattr(self._instance, key, value)
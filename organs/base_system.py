from __future__ import annotations

from pathlib import Path
from ncatbot.plugin_system import EventBus
from typing import TypeVar, Generic

from ..utils import ConfigGenerator

TConfig = TypeVar('TConfig', bound='SystemConfig')

class SystemConfig:
    """基础系统配置基类，子类可扩展字段。

    初始化时：
        - 自动生成缺失的 YAML 配置
        - 然后加载已有配置覆盖默认值
    """

    def __init__(self, work_path: Path, attr_order: list[str]):
        self.attr_order = attr_order
        self._config_generator = ConfigGenerator(work_path, self)
        self._config_generator.generate_config()
        self._config_generator.reload_config()



class BaseSystem(Generic[TConfig]):
    """系统基类，泛型形式绑定具体配置类型。

    用法示例：
        class MySystem(BaseSystem[MyConfig]):
            def __init__(self, event_bus, work_path):
                super().__init__(event_bus, work_path, MyConfig(work_path))
    """

    def __init__(self, event_bus: EventBus, work_path: Path, config: TConfig):
        if not isinstance(config, SystemConfig):  # 运行时兜底校验
            raise TypeError("config 必须是 SystemConfig 的子类实例")
        self._event_bus = event_bus
        self._work_path = work_path
        self._config: TConfig = config

    @property
    def config(self) -> TConfig:
        return self._config

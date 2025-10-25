from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class BotBaseInfo:
    """机器人基础信息，可通过 YAML 修改后热重载"""
    name: str = "月白"
    alias: list[str] = field(default_factory=lambda: ["Sirius"])
    gender: str = "女"
    age: int = 18
    species: str = "人类"
    hobbies: list[str] = field(default_factory=lambda: ["编程", "绘画", "音乐", "游戏", "摄影"])
    personality: list[str] = field(default_factory=lambda: ["聪明", "理智", "幽默"])
    chat_style: list[str] = field(default_factory=lambda: ["少量夹杂网络梗", "适当调侃", "有时用'喵'作语气词"])
    appearance: str = "有着蓝色的长发和蓝色的眼睛，身材高挑纤细，喜欢穿蓝色JK。"
    more_info: str = "无"

    def __init__(self, work_path: Path, someone: Optional[str] = None):
        """初始化机器人基础信息
        
        Args:
            work_path: 工作路径，用于读取配置文件
            someone: 如果指定，则从 simulate_someone/{someone}.txt 加载 chat_style
        """
        # 设置默认值
        self.name = "月白"
        self.alias = ["Sirius"]
        self.gender = "女"
        self.age = 18
        self.species = "人类"
        self.hobbies = ["编程", "绘画", "音乐", "游戏", "摄影"]
        self.personality = ["聪明", "理智", "幽默"]
        self.chat_style = ["少量夹杂网络梗", "适当调侃", "有时用'喵'作语气词"]
        self.appearance = "有着蓝色的长发和蓝色的眼睛，身材高挑纤细，喜欢穿蓝色JK。"
        self.more_info = "无"
        
        self._work_path = work_path
        self._config_path = work_path / "BotBaseInfo.yaml"
        
        # 生成配置文件（如果不存在）
        self._generate_config()
        
        # 从配置文件加载
        self._load_config()
        
        # 如果指定了模拟某人，覆盖 chat_style
        if someone:
            self._load_someone_style(someone)

    def _generate_config(self):
        """生成默认配置文件（如果不存在）"""
        if self._config_path.exists():
            return
        
        config_data = {
            "name": self.name,
            "alias": self.alias,
            "gender": self.gender,
            "age": self.age,
            "species": self.species,
            "hobbies": self.hobbies,
            "personality": self.personality,
            "chat_style": self.chat_style,
            "appearance": self.appearance,
            "more_info": self.more_info,
        }
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f, allow_unicode=True, sort_keys=False)

    def _load_config(self):
        """从 YAML 配置文件加载数据"""
        if not self._config_path.exists():
            return
        
        with open(self._config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not config:
                return
            
            # 更新实例属性
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def _load_someone_style(self, someone: str):
        """从 simulate_someone 目录加载特定人的聊天风格"""
        someone_file = self._work_path / "simulate_someone" / f"{someone}.txt"
        try:
            with open(someone_file, "r", encoding="utf-8") as f:
                self.chat_style = f.read().splitlines()
        except Exception as e:
            raise Exception(f"无法加载名为 {someone} 的信息文件，请确保该文件存在且格式正确。原因: {e}")

    def save_config(self):
        """保存当前配置到 YAML 文件"""
        config_data = {
            "name": self.name,
            "alias": self.alias,
            "gender": self.gender,
            "age": self.age,
            "species": self.species,
            "hobbies": self.hobbies,
            "personality": self.personality,
            "chat_style": self.chat_style,
            "appearance": self.appearance,
            "more_info": self.more_info,
        }
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f, allow_unicode=True, sort_keys=False)

    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()

    def is_mentioned(self, message: str) -> bool:
        """检查消息中是否提及了机器人"""
        message = message.lower()
        if not self.alias:
            return False
        if self.name.lower() in message:
            return True
        for nickname in self.alias:
            if nickname.lower() in message:
                return True
        return False
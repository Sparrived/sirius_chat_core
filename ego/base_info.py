from pathlib import Path
import yaml
import os

from ..utils import ConfigGenerator

class BotBaseInfo:
    """机器人基础信息，可通过 YAML 修改后热重载"""
    name = "月白"
    alias = ["Sirius"]
    gender = "女"
    age = 18
    species = "人类"
    hobbies = ["编程", "绘画", "音乐", "游戏", "摄影"]
    personality = ["聪明", "理智", "可爱", "幽默"]
    chat_style = ["少量夹杂网络梗", "轻松活泼", "适当调侃", "喜欢在句尾加“喵”"]
    appearance = "有着蓝色的长发和蓝色的眼睛，身材高挑纤细，喜欢穿蓝色JK。"

    def __init__(self, work_path: Path):
        self._config_generator = ConfigGenerator(work_path, self)
        self._config_generator.generate_config()
        self._config_generator.reload_config()

    def is_mentioned(self, message: str) -> bool:
        """检查消息中是否提及了机器人"""
        message = message.lower()
        if not self.alias:
            return False
        if self.name in message:
            return True
        for nickname in self.alias:
            if nickname in message:
                return True
        return False
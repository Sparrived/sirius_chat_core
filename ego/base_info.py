from pathlib import Path
import yaml
import os
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
        yaml_path = work_path / "bot_info.yaml"
        if not os.path.exists(yaml_path):
            # 如果文件不存在，则创建一个，内容为当前类的属性
            info = {
                "name": self.name,
                "alias": self.alias,
                "gender": self.gender,
                "age": self.age,
                "species": self.species,
                "hobbies": self.hobbies,
                "personality": self.personality,
                "appearance": self.appearance,
                "chat_style": self.chat_style
            }
            with open(yaml_path, 'w', encoding='utf-8') as f:
                # sort_keys=False 确保按构建 info 时的插入顺序输出
                yaml.safe_dump(info, f, allow_unicode=True, sort_keys=False)
            return
        self.update_bot_info(work_path)

    def update_bot_info(self, work_path: Path):
        """从 YAML 文件更新机器人信息"""
        yaml_path = work_path / "bot_info.yaml"
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not config:
                return
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
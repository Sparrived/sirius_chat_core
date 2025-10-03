from ncatbot.plugin_system import NcatBotPlugin

from .config import SiriusChatCoreConfig
from .ego import BotBaseInfo
class SiriusChatCore(NcatBotPlugin):
    name = "SiriusChatCore"
    version = "1.0.0"
    description = "Sirius的机器人聊天模型中枢插件。"

    def plugin_config_register(self):
        """注册插件配置"""
        config = SiriusChatCoreConfig()
        filtered = [name for name in dir(config) if not name.startswith("__")]
        for name in filtered:
            self.register_config(name, getattr(config, name), value_type=type(getattr(config, name)))

    def model_init(self):
        """模型初始化"""
        self._bot_info = BotBaseInfo(self.workspace)

    async def on_load(self):
        self.plugin_config_register()
        self.model_init()


from ncatbot.plugin_system import NcatBotPlugin, NcatBotEvent, on_message
from ncatbot.core import BaseMessageEvent, GroupMessageEvent, PrivateMessageEvent
from ncatbot.utils import get_log

from .config import SiriusChatCoreConfig
from .ego import BotBaseInfo
class SiriusChatCore(NcatBotPlugin):
    name = "SiriusChatCore"
    version = "0.1.1"
    description = "Sirius的机器人聊天模型中枢插件。"
    log = get_log(name)

    async def on_load(self):
        self.plugin_config_register()
        self.plugin_init()
        self.model_init()

    async def on_reload(self) -> None:
        pass

    async def on_close(self) -> None:
        pass

    @on_message
    async def handle_message(self, event: BaseMessageEvent):
        """处理消息"""
        if isinstance(event, PrivateMessageEvent):
            if not self.config["chat_settings"]["private_chat_mode"]:
                return  # 忽略私聊消息
            source = f"P{event.user_id}"
        elif isinstance(event, GroupMessageEvent):
            if event.group_id not in self.config["subscribed_groups"]:
                return  # 忽略不在启用列表中的群聊消息
            source = f"G{event.group_id}"
        else:
            return  # 忽略其他类型消息
        self.log.debug(f"收到消息，来源: {source}, 内容: {event.raw_message}")

    def _on_chat_functions(self, event: NcatBotEvent):
        """处理聊天功能事件"""
        pass

    def plugin_config_register(self):
        """注册插件配置"""
        config = SiriusChatCoreConfig()
        filtered = [name for name in dir(config) if not name.startswith("__")]
        for name in filtered:
            self.register_config(name, getattr(config, name), value_type=type(getattr(config, name)))

    def plugin_init(self):
        """插件本体功能初始化"""
        self.register_handler("SiriusChatCore.chat_functions", self._on_chat_functions)
        self.log.info("开始监听 SiriusChatCore.chat_functions 事件...")

    def model_init(self):
        """模型初始化"""
        self._bot_info = BotBaseInfo(self.workspace)


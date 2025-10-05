import base64
from ncatbot.plugin_system import NcatBotPlugin, NcatBotEvent, on_message, on_notice
from ncatbot.core import BaseMessageEvent, GroupMessageEvent, PrivateMessageEvent, NoticeEvent
from ncatbot.core.event import At, AtAll, PlainText, Face, Image
from ncatbot.utils import get_log, status
import requests

from .config import SiriusChatCoreConfig
from .ego import BotBaseInfo
from .organs import TalkSystem, MemoticonSystem
from .models import ChatModel, FilterModel, MemoticonModel
from .api_platforms import PLATFORMNAMEMAP
from .message import MessageUnit

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
    
    @on_notice
    async def handle_notice(self, event: NoticeEvent):
        """处理通知"""
        # 处理戳一戳
        if event.notice_type == "notify" and event.sub_type == "poke":
            if event.target_id != event.self_id:
                return  # 不是戳我，忽略
            if event.group_id is None:
                source = f"P{event.user_id}"
                friends = status.global_api.get_friend_list_sync()
                current_friend = next((f for f in friends if f["user_id"] == event.user_id), None)
                if current_friend:
                    user_nickname = current_friend["nickname"]
                    user_card = None
                else:
                    return # 只回复好友的戳一戳
            else:
                source = f"G{event.group_id}"
                user_nickname = status.global_api.get_group_member_info_sync(event.group_id, event.user_id).nickname
                user_card = status.global_api.get_group_member_info_sync(event.group_id, event.user_id).card
            self.log.info(f"收到戳一戳，来源: {source}, 用户ID: {event.user_id}")
            mu = MessageUnit(
                user_nickname=user_nickname,
                user_id=str(event.user_id),
                message=f"你在QQ上被 {user_nickname} 戳一戳戳了一下！",
                time=str(event.time),
                source=source,
                user_card=user_card,
                is_notice=True
            )
            self.talk_system.add_talk(source, mu)

    @on_message
    async def handle_message(self, event: BaseMessageEvent):
        """处理消息"""
        if isinstance(event, PrivateMessageEvent):
            if not self.config["chat_settings"]["private_chat_mode"]:
                return  # 忽略私聊消息
            source = f"P{event.user_id}"
            user_card = None
        elif isinstance(event, GroupMessageEvent):
            if event.group_id not in self.config["subscribed_groups"]:
                return  # 忽略不在启用列表中的群聊消息
            source = f"G{event.group_id}"
            user_card = event.sender.card if event.sender.card else None
        else:
            return  # 忽略其他类型消息
        self.log.debug(f"收到消息，来源: {source}, 内容: {event.raw_message}")
        # ======== 处理表情包 ========
        if len(event.message) == 1 and "summary=&#91;动画表情&#93;" in str(event.raw_message): # CQ码中存在summary=&#91;动画表情&#93;的是用户储存的表情包
            img = event.message.filter_image()[0]
            response = requests.get(img.url)
            response.raise_for_status()
            img_base64 = base64.b64encode(response.content).decode("utf-8")
            self.memoticon_system.judge_meme(img_base64)
            return # 学习完直接跑路，不回复
        # ======== 构造 MessageUnit 并交给 TalkSystem ========
        message = ""
        for seg in event.message:
            if isinstance(seg, At):
                if not isinstance(event, GroupMessageEvent): # 该死的Pylance
                    raise ValueError("这是不可能发生的事情！！！")
                message += f"@{status.global_api.get_group_member_info_sync(event.group_id, seg.qq).nickname} "
            elif isinstance(seg, AtAll):
                if not isinstance(event, GroupMessageEvent):
                    raise ValueError("这是不可能发生的事情！！！")
                message += "@全体成员 "
            elif isinstance(seg, PlainText):
                message += seg.text
            elif isinstance(seg, Face):
                continue  # 忽略QQ表情
            elif isinstance(seg, Image):
                # TODO: 使用VLM处理其它图片
                continue
            else:
                raise ValueError(f"不支持的消息段类型: {type(seg)}，请联系开发者。")
        mu = MessageUnit(
            user_nickname=event.sender.nickname,
            user_id=str(event.user_id),
            message=message,
            time=str(event.time),
            source=source,
            user_card=user_card
        )
        self.talk_system.add_talk(source, mu)

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
        # ======== Chat Model 初始化 ========
        platform_name, model_name = next(iter(self.config["model_settings"]["model_selection"]["ChatModel"].items()))
        chat_model = ChatModel(
            model_name=model_name,
            platform=PLATFORMNAMEMAP[platform_name](self.config["model_settings"]["platforms_apikey"][platform_name]),
            bot_info=self._bot_info
        )
        # ======== Filter Model 初始化 ========
        if self.config["chat_settings"]["filter_mode"]:
            platform_name, model_name = next(iter(self.config["model_settings"]["model_selection"]["FilterModel"].items()))
            filter_model = FilterModel(
                model_name=model_name,
                platform=PLATFORMNAMEMAP[platform_name](self.config["model_settings"]["platforms_apikey"][platform_name])
            )
        else:
            filter_model = None
        # ======== Memoticon Model 初始化 ========
        platform_name, model_name = next(iter(self.config["model_settings"]["model_selection"]["MemoticonModel"].items()))
        memoticon_model = MemoticonModel(
            model_name=model_name,
            platform=PLATFORMNAMEMAP[platform_name](self.config["model_settings"]["platforms_apikey"][platform_name])
        )
        # ======== 系统初始化 ========
        self.talk_system = TalkSystem(self.event_bus, self.workspace, chat_model, filter_model)
        self.memoticon_system = MemoticonSystem(self.event_bus, self.workspace, memoticon_model)


import time

from ..ego.base_info import BotBaseInfo
from .ego_prompt import SELFINFOPROMPT, CHATSTRUCTURELIMITPROMPT, CHATLIMITPROMPT
from .message_prompt import MESSAGEUNITPROMPT
from .model_prompt import CHATTOOLSPROMPT, MEMOTICONPROMPT, FILTERPROMPT

class PromptManager:
    @staticmethod
    def _get_self_info_prompt(bot_info: BotBaseInfo) -> str:
        if bot_info.more_info == "无":
            more_info = f"性格为{'、'.join(x for x in bot_info.personality)}，爱好为{'、'.join(x for x in bot_info.hobbies)}"
        else:
            more_info = bot_info.more_info
        return SELFINFOPROMPT.format(
            bot_info.name,
            "、".join(x for x in bot_info.alias),
            bot_info.gender,
            bot_info.age,
            bot_info.species,
            bot_info.appearance,
            more_info,
            "、".join(x for x in bot_info.chat_style)
        )
    @staticmethod
    def _get_chat_limit_prompt() -> str:
        return CHATLIMITPROMPT.format(str(time.strftime("%Y年%m月%d日 %H:%M", time.localtime())))

    @staticmethod
    def _get_chat_structure_limit_prompt() -> str:
        return CHATSTRUCTURELIMITPROMPT

    @staticmethod
    def get_chat_prompt(bot_info: BotBaseInfo) -> str:
        prompts = [
            PromptManager._get_self_info_prompt(bot_info), # 角色信息
            PromptManager.get_message_unit_prompt(), # 介绍MessageUnit的组成
            PromptManager._get_chat_limit_prompt(), # 聊天时间限制
            PromptManager._get_chat_structure_limit_prompt() # 聊天结构限制
            ]
        prompt = "\n".join(prompts)
        return prompt

    @staticmethod
    def get_message_unit_prompt() -> str:
        return MESSAGEUNITPROMPT

    @staticmethod
    def get_chat_tools_prompt(tools: list[dict]) -> str:
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool['function']['name']}:{tool['function']['description']}")
        return CHATTOOLSPROMPT.format("\n".join(tool_descriptions))
    
    @staticmethod
    def get_memoticon_prompt() -> str:
        return MEMOTICONPROMPT
    
    @staticmethod
    def get_filter_prompt() -> str:
        return FILTERPROMPT
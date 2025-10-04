from ..ego.base_info import BotBaseInfo
from .ego_prompt import SELFINFOPROMPT
from .message_prompt import MESSAGEUNITPROMPT
from .model_prompt import CHATTOOLSPROMPT, MEMOTICONPROMPT, FILTERPROMPT

class PromptManager:
    @staticmethod
    def _get_self_info_prompt(bot_info: BotBaseInfo) -> str:
        return SELFINFOPROMPT.format(
            bot_info.name,
            "、".join(x for x in bot_info.alias),
            bot_info.gender,
            bot_info.age,
            bot_info.species,
            "、".join(x for x in bot_info.hobbies),
            "、".join(x for x in bot_info.personality),
            bot_info.appearance,
            "、".join(x for x in bot_info.chat_style)
        )

    @staticmethod
    def get_chat_prompt(bot_info: BotBaseInfo) -> str:
        prompts = [
            PromptManager._get_self_info_prompt(bot_info), # 角色信息
            PromptManager.get_message_unit_prompt() # 介绍MessageUnit的组成
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
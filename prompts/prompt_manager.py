from ..ego.base_info import BotBaseInfo
from .ego_prompt import SELFINFOPROMPT
from .message_prompt import MESSAGEUNITPROMPT

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

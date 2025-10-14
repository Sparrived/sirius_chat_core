class SiriusChatCoreConfig:
    subscribed_groups = ["244137718"]
    model_settings = {
        "platforms_apikey": {
            "SiliconFlow" : "your_api_key_here",
            "OpenAI" : "your_api_key_here",
            "VolcengineArk" : "your_api_key_here"
        },
        "model_selection": {
            "FilterModel": {"SiliconFlow": "Qwen/Qwen3-30B-A3B"},
            "ChatModel": {"VolcengineArk": "deepseek-v3-1-250821"},
            "MemoticonModel": {"SiliconFlow": "Pro/Qwen/Qwen2.5-VL-7B-Instruct"}
        }
    }
    chat_settings = {
        "filter_mode": False,
        "private_chat_mode": True
    }
    simulate_someone = {
        "enabled": False,
        "someone_name": "某人"
    }
    
import json
import os
from typing import Dict, List

from src.utils.path_utils import resource_path

class PromptManager:
    """
    Prompt 管理器：负责读取、保存和格式化 Prompt 模板。
    """

    # 定义 Prompt 的元数据：显示名称、支持的占位符、默认内容
    PROMPT_DEFS = {
        "role_setup": {
            "name": "角色设定",
            "placeholders": [],
            "default": "你是一个运行在电脑桌面上的虚拟桌宠助手，你的名字叫SteaMiss。你需要用简短、可爱、活泼的语气与用户对话。用户现在的名字是用户。"
        },
        "post_requirements": {
            "name": "后置要求",
            "placeholders": [],
            "default": "请保持回答简短，控制在50字以内。"
        },
        "game_recommendation": {
            "name": "游戏推荐 (被动查询)",
            "placeholders": ["{game_list}", "{user_query}"],
            "default": "目前库里的游戏有：\n{game_list}\n\n请根据用户的需求，从上述列表中推荐合适的游戏，并说明理由。"
        },
        "active_game_recommendation": {
            "name": "主动游戏推荐",
            "placeholders": ["{game_name}", "{appid}", "{playtime_forever}", "{playtime_2weeks}", "{description}"],
            "default": "推荐游戏：{game_name} (AppID: {appid})\n总时长：{playtime_forever}小时\n两周时长：{playtime_2weeks}小时\n简介：{description}\n\n请根据以上信息，用简短、有趣的语气向我推荐这款游戏，并且选取一些信息对我进行吐槽。注意：两周时长为0时，很可能不止两周没玩。"
        },
        "say_hello": {
            "name": "打招呼",
            "placeholders": [
                "{current_datetime}",
                "{persona_name}",
                "{steam_level}",
                "{total_playtime_hours}",
                "{recent_games}",
                "{owned_games_count}",
                "{last_logoff}",
                "{time_created}",
                "{account_age_days}",
            ],
            "default": (
                "用户刚刚向你打了招呼。请结合以下 Steam 档案信息中的一至二条，回复他。"
                "可以轻微吐槽，但不要冒犯或攻击。若信息缺失就自然略过，不要编造。\n\n"
                "【当前时间】{current_datetime}\n"
                "【Steam昵称】{persona_name}\n"
                "【账号等级】Lv. {steam_level}\n"
                "【总游玩时长】{total_playtime_hours} 小时\n"
                "【最近玩过】{recent_games}\n"
                "【拥有游戏数】{owned_games_count}\n"
                "【上次离线】{last_logoff}\n"
                "【账号创建】{time_created}（{account_age_days} 天）\n"
                "\n"
                "请直接输出你要对用户说的话。"
            ),
        }
    }

    def __init__(self):
        # 统一存放在 config/ 目录下
        self.config_path = resource_path("config", "prompts.json")
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        """从文件加载 Prompt，如果文件不存在则使用默认值"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.prompts = json.load(f)
            except Exception as e:
                print(f"[PromptManager] Load failed: {e}")
                self.prompts = {}
        
        # 补全缺失的 key 为默认值
        for key, meta in self.PROMPT_DEFS.items():
            if key not in self.prompts:
                self.prompts[key] = meta["default"]

    def save_prompts(self):
        """保存当前 Prompt 到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[PromptManager] Save failed: {e}")

    def get_prompt(self, key: str, **kwargs) -> str:
        """
        获取并格式化 Prompt。自动组装：角色设定 + 具体功能 Prompt + 后置要求。
        :param key: Prompt 的键名
        :param kwargs: 用于填充占位符的变量
        :return: 格式化后的 Prompt 字符串
        """
        # 1. 获取核心模板
        main_template = self.prompts.get(key, self.PROMPT_DEFS.get(key, {}).get("default", ""))
        
        # 2. 如果是功能性 Prompt（非基础设定），则进行组装
        if key not in ["role_setup", "post_requirements"]:
            role_template = self.prompts.get("role_setup", self.PROMPT_DEFS.get("role_setup", {}).get("default", ""))
            post_template = self.prompts.get("post_requirements", self.PROMPT_DEFS.get("post_requirements", {}).get("default", ""))
            full_template = f"{role_template}\n\n{main_template}\n\n{post_template}"
        else:
            full_template = main_template

        try:
            return full_template.format(**kwargs)
        except KeyError as e:
            print(f"[PromptManager] Missing placeholder for {key}: {e}")
            # 降级：尝试只返回核心模板（可能也不行，但比报错好）
            return main_template
        except Exception as e:
            print(f"[PromptManager] Format error for {key}: {e}")
            return main_template

    def update_prompt(self, key: str, content: str):
        """更新内存中的 Prompt（需手动调用 save_prompts 持久化）"""
        if key in self.PROMPT_DEFS:
            self.prompts[key] = content

    def get_raw_prompt(self, key: str) -> str:
        """获取原始模板字符串（用于编辑）"""
        return self.prompts.get(key, "")

    def get_definitions(self) -> Dict:
        """获取 Prompt 定义元数据"""
        return self.PROMPT_DEFS

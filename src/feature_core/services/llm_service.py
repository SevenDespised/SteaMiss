import requests
import json

class LLMService:
    """
    LLM 服务：使用 requests 调用 OpenAI 兼容接口。
    """
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._is_available = False

    @property
    def is_available(self):
        return self._is_available

    def check_availability(self, api_key=None, base_url=None, model=None):
        """
        检查服务是否可用。
        尝试发送一个极简请求。
        如果提供了参数，则使用参数进行检查（用于设置界面测试）；
        否则使用 config_manager 中的配置（用于启动时检查），并更新 self._is_available 状态。
        """
        is_self_check = (api_key is None and base_url is None and model is None)

        if is_self_check:
            api_key = self.config_manager.get("llm_api_key", "")
            base_url = self.config_manager.get("llm_base_url", "")
            model = self.config_manager.get("llm_model", "")

        if not api_key or not base_url or not model:
            if is_self_check:
                self._is_available = False
            return False

        # 构造测试消息
        messages = [{"role": "user", "content": "Hi"}]
        
        # 复用 chat_completion 的逻辑，但需要能够传入临时配置
        # 为了避免大量重复代码，这里提取一个内部方法或者临时修改配置
        # 由于 chat_completion 强依赖 config_manager，我们这里手动构造请求
        
        # URL 处理逻辑复用
        base_url = base_url.rstrip("/")
        if base_url.endswith("/v1"):
             url = f"{base_url}/chat/completions"
        elif base_url.endswith("/chat/completions"):
             url = base_url
        else:
             url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1  # 限制 token 数，加快响应并节省成本
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            # 只要请求成功，就认为可用
            if is_self_check:
                self._is_available = True
            return True
        except Exception as e:
            print(f"[LLM] Availability check failed: {e}")
            if is_self_check:
                self._is_available = False
            return False

    def chat_completion(self, messages):
        """
        调用 LLM 进行对话。
        @param messages: 消息列表，例如 [{"role": "user", "content": "hello"}]
        @return: 响应文本，如果出错则返回 None
        """
        api_key = self.config_manager.get("llm_api_key", "")
        base_url = self.config_manager.get("llm_base_url", "")
        model = self.config_manager.get("llm_model", "")

        if not api_key or not base_url or not model:
            print("[LLM] Missing configuration")
            return None

        # 确保 base_url 不以 /chat/completions 结尾，也不以 / 结尾
        base_url = base_url.rstrip("/")
        if base_url.endswith("/v1"):
             url = f"{base_url}/chat/completions"
        elif base_url.endswith("/chat/completions"):
             url = base_url
        else:
             # 尝试猜测，如果用户只给了 host
             url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content
        except Exception as e:
            print(f"[LLM] Request failed: {e}")
            return None

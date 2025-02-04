import os
import requests
import threading
import json
from dotenv import load_dotenv, set_key

# 加载 .env 文件
load_dotenv()

# 从 .env 文件中读取配置（不设置默认值，如果不存在则返回空字符串）
CHAT_API_URL = os.getenv('CHAT_API_URL', "")
API_KEY = os.getenv('API_KEY', "")
MODEL = os.getenv('MODEL', "")

SECOND_CHAT_API_URL = os.getenv('SECOND_CHAT_API_URL')
SECOND_API_KEY = os.getenv('SECOND_API_KEY')

ENV_FILE = ".env"  # .env 文件路径

def load_config():
    """
    完全从 .env 文件中加载配置。
    PROMPTS 环境变量中存储的是 JSON 格式的字符串。
    """
    return {
        "api_url": os.getenv('CHAT_API_URL', ""),
        "api_key": os.getenv('API_KEY', ""),
        "model": os.getenv('MODEL', ""),
        "active_prompt": os.getenv('ACTIVE_PROMPT', ""),
        "prompts": json.loads(os.getenv('PROMPTS', "{}"))
    }

def save_config(config):
    """
    保存配置时直接调用 update_dotenv() 更新 .env 文件，
    这样所有配置信息都存储在 .env 文件中。
    """
    update_dotenv(config)

def update_dotenv(new_config):
    """
    将 new_config 中的 API 配置、MODEL、ACTIVE_PROMPT 和 PROMPTS 写入 .env 文件，
    如果 .env 文件不存在则先创建，并更新当前进程的环境变量。
    使用 quote_mode="always" 强制写入引号，确保 MODEL、ACTIVE_PROMPT 和 PROMPTS 变量能正确保存。
    """
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write("")
    new_api_url = new_config.get("api_url", "")
    new_api_key = new_config.get("api_key", "")
    new_model = new_config.get("model", "")
    new_active_prompt = new_config.get("active_prompt", "")
    new_prompts = json.dumps(new_config.get("prompts", {}))
    set_key(ENV_FILE, "CHAT_API_URL", new_api_url)
    set_key(ENV_FILE, "API_KEY", new_api_key)
    set_key(ENV_FILE, "MODEL", new_model, quote_mode="always")
    set_key(ENV_FILE, "ACTIVE_PROMPT", new_active_prompt, quote_mode="always")
    set_key(ENV_FILE, "PROMPTS", new_prompts, quote_mode="always")
    os.environ["CHAT_API_URL"] = new_api_url
    os.environ["API_KEY"] = new_api_key
    os.environ["MODEL"] = new_model
    os.environ["ACTIVE_PROMPT"] = new_active_prompt
    os.environ["PROMPTS"] = new_prompts

class AIChat:
    def __init__(self, use_second_api=False):
        """
        如果 use_second_api 为 True 且存在第二套 API，则使用第二套，
        否则完全依赖 .env 文件中的配置。
        同时加载 PROMPTS 和 MODEL 设置。
        """
        self.use_second_api = use_second_api
        config = load_config()
        if use_second_api and SECOND_CHAT_API_URL and SECOND_API_KEY:
            self.api_url = SECOND_CHAT_API_URL
            self.api_key = SECOND_API_KEY
        else:
            self.api_url = config.get("api_url", "")
            self.api_key = config.get("api_key", "")
        self.model = config.get("model", "")
        self.active_prompt = config.get("active_prompt", "")
        self.prompts = config.get("prompts", {})

    def update_config(self, new_config):
        self.api_url = new_config.get("api_url", self.api_url)
        self.api_key = new_config.get("api_key", self.api_key)
        self.model = new_config.get("model", self.model)
        self.active_prompt = new_config.get("active_prompt", self.active_prompt)
        self.prompts = new_config.get("prompts", self.prompts)
        if not self.use_second_api:
            update_dotenv(new_config)

    def get_response(self, user_message, callback):
        if not self.active_prompt or self.active_prompt not in self.prompts:
            callback("❌ 请先配置 AI 对话的 prompt！")
            return

        prompt_config = self.prompts[self.active_prompt]
        messages = []
        if prompt_config.get("system"):
            messages.append({"role": "system", "content": prompt_config["system"]})
        user_content = (prompt_config.get("user", "") + "\n" + user_message).strip()
        messages.append({"role": "user", "content": user_content})

        def fetch():
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"].strip()
                else:
                    ai_response = f"❌ API 调用失败: {response.status_code} {response.text}"
            except Exception as e:
                ai_response = f"❌ 出错: {e}"
            callback(ai_response)

        threading.Thread(target=fetch, daemon=True).start()

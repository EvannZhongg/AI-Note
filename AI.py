import requests
import threading
import tkinter as tk

CHAT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "API Key"  # 替换成你的 API Key

class AIChat:
    def __init__(self):
        self.api_url = CHAT_API_URL
        self.api_key = API_KEY

    def get_response(self, user_message, callback):
        """
        在后台线程中向 AI 服务器发送请求，并调用 callback 处理结果。
        """
        def fetch():
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "google/gemma-2-9b-it",
                        "messages": [{"role": "user", "content": user_message}]
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

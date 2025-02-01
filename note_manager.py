import tkinter as tk
import json
import os
from tkinter import messagebox

SAVE_FILE = "sticky_notes.json"

class NoteManager:
    def __init__(self, app):
        self.app = app

    def save_note(self):
        """
        保存当前便笺内容：
          仅当文本（包括图片标记）非空时保存；
          保存内容中会包含图片标记（例如 [[IMG:/path/to/image.png]]）。
        """
        content = self.app.text_widget.get("1.0", tk.END).strip()
        if not content:
            # 如果内容为空，则不保存（也可以选择删除已保存的记录）
            return
        data = self.load_notes_list()
        if not isinstance(data, dict):
            data = {}
        note_id_str = str(self.app.note_id)
        data[note_id_str] = {
            "text": content,
            "header_bg": self.app.header_bg
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_note(self):
        """
        加载便笺内容时调用 app.load_content() 处理文本和图片标记，
        从而自动恢复之前插入的图片。
        """
        data = self.load_notes_list()
        if self.app.note_id in data:
            note = data[self.app.note_id]
            self.app.load_content(note.get("text", ""))
            self.app.header_bg = note.get("header_bg", self.app.header_bg)
            self.app.header.config(bg=self.app.header_bg)

    @staticmethod
    def load_notes_list():
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️ JSON 文件损坏，自动重置：{e}")
                return {}
        return {}

    def delete_note(self):
        if messagebox.askyesno("删除便笺", "确定删除此便笺吗？"):
            data = self.load_notes_list()
            if self.app.note_id in data:
                del data[self.app.note_id]
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            self.app.root.destroy()

    def new_note(self):
        # 在本多进程方案中，新建便笺由全局命令队列处理，不使用此方法
        pass

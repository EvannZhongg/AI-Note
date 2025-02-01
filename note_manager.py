import tkinter as tk
import json
import os
from tkinter import messagebox

SAVE_FILE = "sticky_notes.json"

class NoteManager:
    def __init__(self, app):
        self.app = app

    def save_note(self):
        """确保存储的 JSON 格式正确"""
        data = self.load_notes_list()
        if not isinstance(data, dict):
            data = {}
        note_id_str = str(self.app.note_id)
        data[note_id_str] = {
            "text": self.app.text_widget.get("1.0", tk.END).strip(),
            "header_bg": self.app.header_bg
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_note(self):
        """加载便笺内容"""
        data = self.load_notes_list()
        if self.app.note_id in data:
            note = data[self.app.note_id]
            self.app.text_widget.insert("1.0", note.get("text", ""))
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
        """删除当前便笺"""
        if messagebox.askyesno("删除便笺", "确定删除此便笺吗？"):
            data = self.load_notes_list()
            if self.app.note_id in data:
                del data[self.app.note_id]
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            self.app.root.destroy()

    def new_note(self):
        # 在多进程方案中，新建便笺由全局命令队列处理，不再使用此方法
        pass

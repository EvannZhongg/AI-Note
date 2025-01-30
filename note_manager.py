import tkinter as tk
import json
import os
from tkinter import messagebox

SAVE_FILE = "sticky_notes.json"

class NoteManager:
    def __init__(self, app):
        self.app = app

    def save_note(self):
        """保存当前便笺"""
        data = self.load_notes_list()  # ✅ 确保获取的是字典

        if not isinstance(data, dict):  # 预防错误
            data = {}

        data[self.app.note_id] = {  # ✅ 确保 `data` 是字典
            "text": self.app.text_widget.get("1.0", tk.END).strip(),
            "header_bg": self.app.header_bg
        }

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_note(self):
        """加载便笺"""
        data = self.load_notes_list()
        if self.app.note_id in data:
            note = data[self.app.note_id]
            self.app.text_widget.insert("1.0", note.get("text", ""))
            self.app.header_bg = note.get("header_bg", self.app.header_bg)
            self.app.header.config(bg=self.app.header_bg)

    @staticmethod
    def load_notes_list():
        """加载所有便笺"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):  # 确保返回的是字典
                        return data
            except json.JSONDecodeError as e:
                print(f"Error reading JSON file: {e}")
                return {}  # 返回空字典，避免崩溃
        return {}  # 返回空字典，如果文件不存在

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
        """新建一个便笺，继承当前样式"""
        from StickyNote import StickyNote  # ✅ 修正导入
        new_window = tk.Toplevel(self.app.root)
        new_window.overrideredirect(True)

        new_note = StickyNote(new_window)
        new_note.header_bg = self.app.header_bg
        new_note.header.config(bg=self.app.header_bg)

        return new_note


import tkinter as tk
import json
import os
import re
from tkinter import messagebox

SAVE_FILE = "sticky_notes.json"

class NoteManager:
    def __init__(self, app):
        self.app = app

    @staticmethod
    def load_notes_list():
        """读取所有便笺的 JSON 文件"""
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

    @staticmethod
    def cleanup_unused_images():
        """
        遍历所有便笺，收集其中的 [[IMG:...]] 路径，与 sticky_notes_images 文件夹下的文件对比，
        如果有文件不在引用列表中，则删除它。
        """
        from Note import IMAGE_FOLDER  # 确保 StickyNote.py 中定义: IMAGE_FOLDER = "sticky_notes_images"
        data = NoteManager.load_notes_list()
        all_references = set()

        # 收集所有便笺中的图片引用
        pattern = re.compile(r"\[\[IMG:(.*?)\]\]")
        for note_id, note_info in data.items():
            text = note_info.get("text", "")
            # 找到所有 [[IMG:xxx]] 并加入 all_references
            matches = pattern.findall(text)
            for m in matches:
                # m 可能是绝对路径或相对路径，先做一下处理
                # 如果你写入 JSON 时就是绝对路径，则直接使用 os.path.exists(m) 即可
                possible_abs = os.path.abspath(m)
                if os.path.exists(possible_abs):
                    # 如果文件确实存在，就用绝对路径存储到 all_references
                    all_references.add(os.path.abspath(possible_abs))
                else:
                    # 如果采用了相对路径（相对于 IMAGE_FOLDER），可以尝试拼接
                    alt_path = os.path.abspath(os.path.join(IMAGE_FOLDER, m))
                    if os.path.exists(alt_path):
                        all_references.add(alt_path)

        # 在文件夹 sticky_notes_images 中逐个文件检查是否依然被引用
        if os.path.exists(IMAGE_FOLDER) and os.path.isdir(IMAGE_FOLDER):
            for f in os.listdir(IMAGE_FOLDER):
                full_path = os.path.abspath(os.path.join(IMAGE_FOLDER, f))
                # 如果此文件不在 all_references 中，则删除
                if full_path not in all_references:
                    try:
                        os.remove(full_path)
                        print(f"已删除未被引用的图片: {full_path}")
                    except Exception as e:
                        print(f"删除图片失败: {full_path}，原因: {e}")

    def save_note(self):
        """
        保存便笺内容后，调用 cleanup_unused_images 清理不再使用的图片。
        """
        content = self.app.text_widget.get("1.0", tk.END).strip()
        if not content:
            # 如果内容为空，则不保存（也可以选择删除已保存的记录）
            return

        data = self.load_notes_list()
        if not isinstance(data, dict):
            data = {}

        note_id_str = str(self.app.note_id)
        existing = data.get(note_id_str, {})
        name = existing.get("name", None)

        # 更新数据
        data[note_id_str] = {
            "text": content,
            "header_bg": self.app.header_bg
        }
        # 如果原记录中有 "name"，保留
        if name is not None:
            data[note_id_str]["name"] = name

        # 写入 JSON 文件
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # 保存后清理不再使用的图片
        self.cleanup_unused_images()

    def load_note(self):
        """
        加载便笺内容，调用 app.load_content() 处理文本和图片标记，
        从而自动恢复之前插入的图片。
        """
        data = self.load_notes_list()
        if self.app.note_id in data:
            note = data[self.app.note_id]
            self.app.load_content(note.get("text", ""))
            self.app.header_bg = note.get("header_bg", self.app.header_bg)
            self.app.header.config(bg=self.app.header_bg)

    def delete_note(self):
        """
        删除当前便笺后，调用 cleanup_unused_images 清理不再使用的图片。
        """
        if messagebox.askyesno("删除便笺", "确定删除此便笺吗？"):
            data = self.load_notes_list()
            if self.app.note_id in data:
                del data[self.app.note_id]
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            self.app.root.destroy()
            # 删除后清理不再使用的图片
            self.cleanup_unused_images()

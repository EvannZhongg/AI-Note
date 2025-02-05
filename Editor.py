#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import re
import shutil

# 使用说明文件路径与图片存放目录
USAGE_FILE = "usage.txt"
IMAGE_FOLDER = "sticky_notes_images"

class UsageEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("使用说明编辑器")
        self.master.geometry("300x400+100+100")
        self.master.configure(bg="#f0f0f0")

        # 工具栏：包含“插入图片”和“保存”按钮
        toolbar = tk.Frame(self.master, bg="#d0d0d0", height=30)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        open_img_btn = tk.Button(toolbar, text="插入图片", command=self.insert_image_marker)
        open_img_btn.pack(side=tk.LEFT, padx=5, pady=2)
        save_btn = tk.Button(toolbar, text="保存", command=self.save_usage)
        save_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        # 创建带滚动条的文本编辑区
        frame = tk.Frame(self.master)
        frame.pack(fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(frame, wrap="word", font=("微软雅黑", 11), undo=True,
                            yscrollcommand=self.scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text.yview)

        # 保存对图片对象的引用，防止图片被垃圾回收
        self.image_refs = []

        # 加载使用说明内容
        self.load_usage()

    def load_usage(self):
        """ 加载 USAGE_FILE 文件内容，并解析插入图片 """
        if not os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                f.write("请在此处编写使用说明，支持图片插入，例如 [[IMG:sticky_notes_images/example.png]]")

        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.image_refs = {}  # 确保是字典，而不是列表

        base_dir = os.path.dirname(os.path.abspath(__file__))

        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)

        for i, part in enumerate(parts):
            if i % 2 == 0:
                self.text.insert(tk.END, part)
            else:
                img_marker = part.strip().replace("\\", "/")  # 统一路径格式

                if "/" not in img_marker and os.sep not in img_marker:
                    img_marker = os.path.join(IMAGE_FOLDER, img_marker)

                img_marker = os.path.normpath(img_marker)

                if not os.path.isabs(img_marker):
                    img_path = os.path.join(base_dir, img_marker)
                else:
                    img_path = img_marker

                if not os.path.exists(img_path):
                    print(f"图片未找到: {img_path}")  # 调试
                    self.text.insert(tk.END, f"[图片加载失败: {img_marker}]\n")
                    continue

                try:
                    with Image.open(img_path) as image:
                        image = image.copy()  # 复制，防止文件锁定

                        max_width = 300
                        if image.width > max_width:
                            ratio = max_width / image.width
                            new_size = (max_width, int(image.height * ratio))
                            image = image.resize(new_size, Image.LANCZOS)

                    photo = ImageTk.PhotoImage(image)
                    self.image_refs[img_path] = photo  # ✅ 确保是字典存储
                    self.text.image_create(tk.END, image=photo)
                    self.text.insert(tk.END, "\n")
                except Exception as e:
                    print(f"图片读取失败: {img_path}, 错误: {e}")
                    self.text.insert(tk.END, f"[图片加载失败:{img_marker}]\n")

        self.text.config(state="normal")

    def insert_image_marker(self):
        """
        打开文件对话框选择图片，
        将所选图片复制到 IMAGE_FOLDER 中（如果不存在则创建），
        然后在文本中插入图片标记，格式为 [[sticky_notes_images/文件名]]
        """
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if file_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            image_folder_path = os.path.join(base_dir, IMAGE_FOLDER)
            if not os.path.exists(image_folder_path):
                os.makedirs(image_folder_path)
            filename = os.path.basename(file_path)
            dest_path = os.path.join(image_folder_path, filename)
            if not os.path.exists(dest_path):
                try:
                    shutil.copy(file_path, dest_path)
                except Exception as e:
                    messagebox.showerror("错误", f"复制图片失败：{e}")
                    return
            # 插入图片标记使用相对路径（统一使用正斜杠）
            marker = f"[[IMG:{IMAGE_FOLDER}/{filename}]]"
            self.text.insert(tk.INSERT, marker)

    def save_usage(self):
        """将文本编辑区的内容保存到 USAGE_FILE 文件中"""
        content = self.text.get("1.0", tk.END)
        try:
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("保存成功", "使用说明已成功保存！")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存使用说明时出错：{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = UsageEditor(root)
    root.mainloop()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import re

USAGE_FILE = "usage.txt"
IMAGE_FOLDER = "sticky_notes_images"

class UsageEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("使用说明编辑器")
        self.master.geometry("300x400+100+100")
        self.master.configure(bg="#f0f0f0")

        # 创建工具栏：包含“打开图片”按钮和“保存”按钮
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

        # 尝试加载使用说明内容
        self.load_usage()

        # 保持对插入的图片引用（如果在文本中显示图片）
        self.image_refs = []

    def load_usage(self):
        """加载 USAGE_FILE 文件内容到文本编辑区，如果文件不存在则创建并写入默认内容。"""
        if not os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                f.write("请在此处编写使用说明，支持图片插入，例如 [[IMG:example.png]]")
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # 清空文本控件
        self.text.delete("1.0", tk.END)
        # 使用正则表达式拆分文本和图片标记
        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                self.text.insert(tk.END, part)
            else:
                # part 为图片路径，尝试加载图片并显示（缩放至合适尺寸）
                img_path = part.strip()
                if not os.path.exists(img_path):
                    # 如果直接路径不存在，尝试从 IMAGE_FOLDER 下查找
                    alt_path = os.path.join(IMAGE_FOLDER, img_path)
                    if os.path.exists(alt_path):
                        img_path = alt_path
                try:
                    image = Image.open(img_path)
                    max_width = 300
                    if image.width > max_width:
                        ratio = max_width / image.width
                        new_size = (max_width, int(image.height * ratio))
                        image = image.resize(new_size, Image.ANTIALIAS)
                    photo = ImageTk.PhotoImage(image)
                    self.text.image_create(tk.END, image=photo)
                    self.text.insert(tk.END, "\n")
                    self.image_refs.append(photo)  # 保持引用
                except Exception as e:
                    self.text.insert(tk.END, f"[图片加载失败:{img_path}]\n")

    def insert_image_marker(self):
        """打开文件对话框选择图片，并在文本光标位置插入图片标记"""
        file_path = filedialog.askopenfilename(title="选择图片",
                                               filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            # 可选择将图片复制到 IMAGE_FOLDER 目录（这里简单直接使用原路径）
            marker = f"[[IMG:{os.path.basename(file_path)}]]"
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

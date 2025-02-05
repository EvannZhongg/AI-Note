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
IMAGE_FOLDER = "Media Files"


class UsageEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("使用说明编辑器")
        self.master.geometry("325x400+100+100")
        self.master.configure(bg="#f0f0f0")

        # 工具栏
        toolbar = tk.Frame(self.master, bg="#d0d0d0", height=30)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        open_img_btn = tk.Button(toolbar, text="插入图片", command=self.insert_image_marker)
        open_img_btn.pack(side=tk.LEFT, padx=5, pady=2)
        save_btn = tk.Button(toolbar, text="保存", command=self.save_usage)
        save_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        # 文本编辑区
        frame = tk.Frame(self.master)
        frame.pack(fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(frame, wrap="word", font=("微软雅黑", 11), undo=True,
                            yscrollcommand=self.scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text.yview)

        # 设置隐藏图片路径的样式
        self.text.tag_configure("hidden", foreground="#f0f0f0")  # 文字颜色设为白色（隐藏）

        # 保存对图片对象的引用，防止垃圾回收
        self.image_refs = []

        # 加载使用说明
        self.load_usage()

    def load_usage(self):
        """ 读取 `USAGE_FILE` 并解析 `[[IMG:xxx]]`，加载文本和图片 """
        if not os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                f.write("请在此处编写使用说明，支持图片插入，例如 [[IMG:Media Files/example.png]]")

        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.image_refs.clear()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)

        for i, part in enumerate(parts):
            if i % 2 == 0:
                self.text.insert(tk.END, part.strip())  # 去掉文本部分的多余换行
            else:
                img_marker = part.strip().replace("\\", "/")  # 统一路径格式
                self.insert_image_in_text(img_marker)  # 直接插入图片，不额外换行

        self.text.config(state="normal")

    def insert_image_marker(self):
        """
        选择图片并插入，确保 `tk.Text` 中可见，同时在文本中插入 `[[IMG:xxx]]`
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

            # 复制图片到 Media Files 文件夹
            if not os.path.exists(dest_path):
                try:
                    shutil.copy(file_path, dest_path)
                except Exception as e:
                    messagebox.showerror("错误", f"复制图片失败：{e}")
                    return

            # 插入图片，同时插入隐藏文本
            self.insert_image_in_text(f"{IMAGE_FOLDER}/{filename}")

    def insert_image_in_text(self, img_marker):
        """
        在 `tk.Text` 插入图片，并插入 `[[IMG:xxx]]` 但隐藏路径
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, img_marker)

        if not os.path.exists(img_path):
            self.text.insert(tk.END, f"[图片加载失败: {img_marker}]\n")
            return

        try:
            image = Image.open(img_path)
            max_width = 300
            if image.width > max_width:
                ratio = max_width / image.width
                new_size = (max_width, int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)

            photo = ImageTk.PhotoImage(image)

            # 插入图片，去掉额外的换行
            self.text.image_create(tk.END, image=photo)  # 插入图片

            # 插入隐藏文本标记（在同一行），避免额外换行
            start_idx = self.text.index(tk.END)  # 记录插入前的位置
            self.text.insert(tk.END, f"[[IMG:{img_marker}]]")
            end_idx = self.text.index(tk.END)  # 记录插入后的位置

            # 让 `[[IMG:xxx]]` 变成白色（隐藏），并放在同一行
            self.text.tag_add("hidden", start_idx, end_idx)

            self.image_refs.append(photo)  # 保持图片引用，防止垃圾回收
        except Exception as e:
            self.text.insert(tk.END, f"[图片加载失败: {img_marker}]\n")

    def save_usage(self):
        """
        保存使用说明文本，确保保留 `[[IMG:xxx]]` 以便下次加载
        """
        content = self.text.get("1.0", tk.END).strip()

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

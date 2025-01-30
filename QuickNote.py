import tkinter as tk
from tkinter import filedialog, Menu, font, colorchooser
from PIL import Image, ImageTk, ImageGrab
import json
import os

SAVE_FILE = "sticky_notes.json"  # 存储便笺的文件
IMAGE_FOLDER = "sticky_notes_images"  # 存放图片的文件夹

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)  # 确保文件夹存在

class StickyNote:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 便笺")
        self.root.geometry("300x400")
        self.root.configure(bg="#1E1E1E")  # 设置暗色背景
        self.root.overrideredirect(True)  # 移除窗口边框

        # 便笺颜色
        self.note_bg = "#333333"  # 默认深色模式
        self.text_fg = "#ffffff"  # 文字颜色

        # 顶部工具栏
        self.header = tk.Frame(self.root, bg="#FFCC00", height=30)
        self.header.pack(fill=tk.X, side=tk.TOP)

        # 关闭按钮
        self.close_btn = tk.Button(self.header, text="X", command=self.close_note, bg="red", fg="white", bd=0, padx=5)
        self.close_btn.pack(side=tk.RIGHT, padx=5)

        # 颜色更改按钮
        self.color_btn = tk.Button(self.header, text="🎨", command=self.change_color, bg="#FFCC00", fg="black", bd=0)
        self.color_btn.pack(side=tk.RIGHT, padx=5)

        # 插入图片按钮
        self.image_btn = tk.Button(self.header, text="📷", command=self.insert_image, bg="#FFCC00", fg="black", bd=0)
        self.image_btn.pack(side=tk.RIGHT, padx=5)

        # 主要的文本输入框
        self.text_widget = tk.Text(self.root, wrap="word", font=("Arial", 14), fg=self.text_fg, bg=self.note_bg,
                                   borderwidth=0, insertbackground="white")
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 绑定粘贴快捷键
        self.root.bind("<Control-v>", self.paste)

        # 右键菜单
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="删除", command=self.close_note)
        self.text_widget.bind("<Button-3>", self.show_context_menu)

        # 存储图片引用
        self.image_refs = []

        # 读取便笺内容
        self.load_notes()

    def change_color(self):
        """更改便笺颜色"""
        color = colorchooser.askcolor()[1]  # 选择颜色
        if color:
            self.note_bg = color
            self.text_widget.config(bg=self.note_bg)

    def close_note(self):
        """关闭便笺并保存"""
        self.save_notes()
        self.root.destroy()

    def show_context_menu(self, event):
        """右键菜单"""
        self.menu.post(event.x_root, event.y_root)

    def paste(self, event=None):
        """粘贴文本或图片"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.text_widget.insert(tk.INSERT, clipboard_content)
        except:
            # 尝试粘贴图片
            try:
                image = ImageGrab.grabclipboard()
                if isinstance(image, Image.Image):
                    self.insert_pil_image(image)
            except Exception as e:
                print("粘贴失败:", e)

    def insert_image(self):
        """插入本地图片"""
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            image = Image.open(file_path)
            self.insert_pil_image(image, file_path)

    def insert_pil_image(self, image, image_path=None):
        """将 PIL 图片插入便笺"""
        image.thumbnail((200, 200))  # 调整大小
        photo = ImageTk.PhotoImage(image)

        self.image_refs.append(photo)  # 保持引用，防止被垃圾回收

        self.text_widget.image_create(tk.INSERT, image=photo)
        self.text_widget.insert(tk.INSERT, "\n")  # 插入换行符

        # 保存图片
        if not image_path:
            image_path = os.path.join(IMAGE_FOLDER, f"image_{len(self.image_refs)}.png")
            image.save(image_path)

        # 记录图片路径
        self.image_refs.append({"image": photo, "path": image_path})

    def save_notes(self):
        """保存便笺内容和图片路径"""
        text_content = self.text_widget.get("1.0", tk.END).strip()

        # 获取所有图片路径
        image_paths = [ref["path"] for ref in self.image_refs if isinstance(ref, dict) and "path" in ref]

        data = [{"text": text_content, "bg": self.note_bg, "images": image_paths}]

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_notes(self):
        """加载便笺内容和图片"""
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                # 处理 `data` 是 `list` 的情况
                if isinstance(data, list) and data:
                    latest_note = data[-1]  # 获取最新的便笺数据
                    self.text_widget.insert("1.0", latest_note.get("text", ""))
                    self.note_bg = latest_note.get("bg", self.note_bg)
                    self.text_widget.config(bg=self.note_bg)

                    # 加载图片
                    if "images" in latest_note:
                        for img_path in latest_note["images"]:
                            if os.path.exists(img_path):
                                image = Image.open(img_path)
                                self.insert_pil_image(image, img_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = StickyNote(root)

    # 退出时保存
    root.protocol("WM_DELETE_WINDOW", app.save_notes)

    root.mainloop()

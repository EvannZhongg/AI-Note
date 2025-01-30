import tkinter as tk
from tkinter import filedialog, Menu, font, colorchooser
from PIL import Image, ImageTk, ImageGrab
import json
import os

SAVE_FILE = "sticky_notes.json"
IMAGE_FOLDER = "sticky_notes_images"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

class StickyNote:
    def __init__(self, root):
        self.root = root
        self.root.geometry("300x400")
        self.root.configure(bg="#2B2B2B")
        self.root.overrideredirect(True)

        # 便笺默认颜色（仅影响顶部栏）
        self.header_bg = "#FFCC00"  # 仅顶部栏颜色
        self.text_bg = "#3E3E3E"  # 文本区域颜色
        self.text_fg = "#FFFFFF"  # 文本颜色

        # 使窗口可以拖动
        self.offset_x = 0
        self.offset_y = 0

        # 创建自定义标题栏
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.on_move)

        # 关闭按钮
        self.close_btn = tk.Button(self.header, text="✖", command=self.close_note, bg="red", fg="white", bd=0,
                                   padx=5, font=("Arial", 12, "bold"), relief="flat", activebackground="darkred")
        self.close_btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 颜色更改按钮（仅修改顶部栏）
        self.color_btn = tk.Button(self.header, text="🎨", command=self.change_color, bg=self.header_bg, fg="black",
                                   bd=0, font=("Arial", 12), relief="flat", activebackground="#FFD700")
        self.color_btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 插入图片按钮
        self.image_btn = tk.Button(self.header, text="📷", command=self.insert_image, bg=self.header_bg, fg="black",
                                   bd=0, font=("Arial", 12), relief="flat", activebackground="#FFD700")
        self.image_btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 主要的文本输入框（始终深色）
        self.text_widget = tk.Text(self.root, wrap="word", font=("Arial", 14), fg=self.text_fg, bg=self.text_bg,
                                   borderwidth=0, insertbackground="white", relief="flat", padx=10, pady=10)
        self.text_widget.pack(fill=tk.BOTH, expand=True)

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

    def start_move(self, event):
        """开始拖动窗口"""
        self.offset_x = event.x
        self.offset_y = event.y

    def on_move(self, event):
        """拖动窗口"""
        x = self.root.winfo_x() + event.x - self.offset_x
        y = self.root.winfo_y() + event.y - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def change_color(self):
        """仅修改顶部工具栏颜色"""
        color = colorchooser.askcolor()[1]
        if color:
            self.header_bg = color  # 仅修改顶部栏颜色
            self.header.config(bg=self.header_bg)
            self.color_btn.config(bg=self.header_bg)
            self.image_btn.config(bg=self.header_bg)

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
        image.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(image)

        self.image_refs.append(photo)

        self.text_widget.image_create(tk.INSERT, image=photo)
        self.text_widget.insert(tk.INSERT, "\n")

        if not image_path:
            image_path = os.path.join(IMAGE_FOLDER, f"image_{len(self.image_refs)}.png")
            image.save(image_path)

        self.image_refs.append({"image": photo, "path": image_path})

    def save_notes(self):
        """保存便笺内容和图片路径"""
        text_content = self.text_widget.get("1.0", tk.END).strip()

        image_paths = [ref["path"] for ref in self.image_refs if isinstance(ref, dict) and "path" in ref]

        data = [{"text": text_content, "header_bg": self.header_bg, "images": image_paths}]

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_notes(self):
        """加载便笺内容和图片"""
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, list) and data:
                    latest_note = data[-1]
                    self.text_widget.insert("1.0", latest_note.get("text", ""))
                    self.header_bg = latest_note.get("header_bg", self.header_bg)

                    self.header.config(bg=self.header_bg)
                    self.color_btn.config(bg=self.header_bg)
                    self.image_btn.config(bg=self.header_bg)

                    if "images" in latest_note:
                        for img_path in latest_note["images"]:
                            if os.path.exists(img_path):
                                image = Image.open(img_path)
                                self.insert_pil_image(image, img_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = StickyNote(root)

    root.protocol("WM_DELETE_WINDOW", app.save_notes)

    root.mainloop()

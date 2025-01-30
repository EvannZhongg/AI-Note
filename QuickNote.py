import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import tempfile

class SimpleNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title("简易便笺")
        self.text_area = tk.Text(self.root, wrap="word", undo=True)  # 启用撤销功能
        self.text_area.pack(expand=True, fill="both")

        # 创建菜单栏
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # 文件菜单
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=self.file_menu)
        self.file_menu.add_command(label="新建", command=self.new_file, accelerator="Ctrl+N")
        self.file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        self.file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")

        # 编辑菜单
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="编辑", menu=self.edit_menu)
        self.edit_menu.add_command(label="撤销", command=self.text_area.edit_undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="重做", command=self.text_area.edit_redo, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="剪切", command=self.cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="复制", command=self.copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="粘贴", command=self.paste, accelerator="Ctrl+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="全选", command=self.select_all, accelerator="Ctrl+A")
        self.edit_menu.add_command(label="插入图片", command=self.insert_image)

        # 绑定快捷键
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-q>", lambda event: self.root.quit())
        self.root.bind("<Control-z>", lambda event: self.text_area.edit_undo())
        self.root.bind("<Control-y>", lambda event: self.text_area.edit_redo())
        self.root.bind("<Control-x>", lambda event: self.cut())
        self.root.bind("<Control-c>", lambda event: self.copy())
        self.root.bind("<Control-v>", lambda event: self.paste())
        self.root.bind("<Control-a>", lambda event: self.select_all())

        # 用于存储当前选中的图片
        self.current_image = None

    def new_file(self):
        self.text_area.delete(1.0, tk.END)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "r") as file:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, file.read())

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))

    def cut(self):
        self.copy()
        if self.text_area.tag_ranges(tk.SEL):
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)

    def copy(self):
        if self.text_area.tag_ranges(tk.SEL):
            try:
                # 获取选中的图片
                index = self.text_area.index(tk.SEL_FIRST)
                image_name = self.text_area.image_names(index)
                if image_name:
                    # 将图片保存到临时文件
                    self.current_image = self.text_area.image_get(image_name)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                        self.current_image.write(tmp_file.name, format="png")
                        self.root.clipboard_clear()
                        self.root.clipboard_append(tmp_file.name)
            except tk.TclError:
                # 如果没有选中图片，则复制文本
                self.text_area.event_generate("<<Copy>>")
        else:
            self.text_area.event_generate("<<Copy>>")

    def paste(self):
        try:
            # 尝试从剪切板获取图片路径
            clipboard_content = self.root.clipboard_get()
            if os.path.exists(clipboard_content):
                # 插入图片
                image = Image.open(clipboard_content)
                image.thumbnail((200, 200))  # 调整图片大小
                photo = ImageTk.PhotoImage(image)
                self.text_area.image_create(tk.INSERT, image=photo)
                self.text_area.image = photo  # 保持对图片的引用
            else:
                # 插入文本
                self.text_area.event_generate("<<Paste>>")
        except tk.TclError:
            # 如果剪切板中没有图片，则插入文本
            self.text_area.event_generate("<<Paste>>")

    def select_all(self):
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        return "break"  # 阻止默认行为

    def insert_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif"), ("所有文件", "*.*")])
        if file_path:
            image = Image.open(file_path)
            image.thumbnail((200, 200))  # 调整图片大小
            photo = ImageTk.PhotoImage(image)
            self.text_area.image_create(tk.END, image=photo)
            self.text_area.insert(tk.END, "\n")  # 插入换行符
            self.text_area.image = photo  # 保持对图片的引用，防止被垃圾回收

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleNotepad(root)
    root.mainloop()

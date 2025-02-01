from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab
import os
import time

IMAGE_FOLDER = "sticky_notes_images"

class ImageHandler:
    def __init__(self, app):
        self.app = app
        self.image_refs = []

    def handle_image_paste(self):
        """
        当外部（text_shortcuts）未能获取文本时，调用此函数尝试粘贴图片。
        若检测到剪贴板中有图片，则保存并插入到文本中。
        """
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                folder = IMAGE_FOLDER
                if not os.path.exists(folder):
                    os.makedirs(folder)
                filename = os.path.join(folder, f"{int(time.time())}.png")
                image.save(filename)
                self.insert_pil_image(image, filename)
        except Exception as e:
            print("粘贴失败(图片):", e)

    def insert_image(self):
        """
        通过文件对话框选择图片后插入图片，同时在文本中插入图片标记（并隐藏该标记）。
        """
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            image = Image.open(file_path)
            self.insert_pil_image(image, file_path)

    def insert_pil_image(self, image, image_path=None, add_newline=True):
        """
        将 PIL Image 对象转换为 PhotoImage 插入文本中。
        如果提供了 image_path，则在图片后插入一个特殊标记：[[IMG:路径]]。
        并为该标记添加 "invisible" 标签，使其不显示在窗口中。

        参数:
          add_newline: 如果为 True，则在图片后自动插入一个换行符（默认用于粘贴操作）。
                       如果为 False，则不自动添加换行符（在从保存内容中加载时使用）。
        """
        image.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(image)
        self.image_refs.append(photo)

        # 在当前插入点插入图片
        self.app.text_widget.image_create("insert", image=photo)

        if image_path:
            marker = f"[[IMG:{image_path}]]"
            self.app.text_widget.insert("insert", marker, ("invisible",))

        if add_newline:
            self.app.text_widget.insert("insert", "\n")

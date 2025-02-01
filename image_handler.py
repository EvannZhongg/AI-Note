from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab
import os
import time

IMAGE_FOLDER = "sticky_notes_images"

class ImageHandler:
    def __init__(self, app):
        self.app = app
        self.image_refs = []

    def paste(self, event=None):
        """
        处理 Ctrl+V 粘贴操作：
        1. 尝试获取剪贴板文本，若成功则插入文本；
        2. 若剪贴板中没有文本，则尝试获取图片，
           如果检测到图片则将其保存到本地（sticky_notes_images 文件夹下），
           并调用 insert_pil_image() 插入图片，同时在文本中插入图片标记（但该标记被隐藏）。
        """
        try:
            clipboard_content = self.app.root.clipboard_get()
            self.app.text_widget.insert("insert", clipboard_content)
        except Exception:
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
                print("粘贴失败:", e)

    def insert_image(self):
        """
        通过文件对话框选择图片后插入图片，同时在文本中插入图片标记（并隐藏该标记）。
        """
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            image = Image.open(file_path)
            self.insert_pil_image(image, file_path)

    def insert_pil_image(self, image, image_path=None):
        """
        将 PIL Image 对象转换为 PhotoImage 插入文本中，
        如果提供了 image_path，则在图片后插入一个特殊标记（格式为 [[IMG:图片路径]]），
        并为该标记添加 "invisible" 标签，使其不显示在窗口中。
        """
        image.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(image)
        self.image_refs.append(photo)
        # 在当前插入点插入图片
        self.app.text_widget.image_create("insert", image=photo)
        if image_path:
            marker = f"[[IMG:{image_path}]]"
            # 插入 marker 后立即为其添加 "invisible" 标签
            self.app.text_widget.insert("insert", marker, ("invisible",))
        self.app.text_widget.insert("insert", "\n")

from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab

IMAGE_FOLDER = "sticky_notes_images"

class ImageHandler:
    def __init__(self, app):
        self.app = app
        self.image_refs = []

    def paste(self, event=None):
        try:
            clipboard_content = self.app.root.clipboard_get()
            self.app.text_widget.insert("insert", clipboard_content)
        except:
            try:
                image = ImageGrab.grabclipboard()
                if isinstance(image, Image.Image):
                    self.insert_pil_image(image)
            except Exception as e:
                print("粘贴失败:", e)

    def insert_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            image = Image.open(file_path)
            self.insert_pil_image(image, file_path)

    def insert_pil_image(self, image, image_path=None):
        image.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(image)
        self.image_refs.append(photo)
        self.app.text_widget.image_create("insert", image=photo)
        self.app.text_widget.insert("insert", "\n")

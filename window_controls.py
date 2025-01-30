from tkinter import colorchooser

class WindowControls:
    def __init__(self, app):
        self.app = app
        self.bind_controls()

    def bind_controls(self):
        """确保所有按钮都已创建后绑定"""
        self.app.close_btn.config(command=self.app.hide_window)
        self.app.pin_btn.config(command=self.toggle_pin)
        self.app.color_btn.config(command=self.change_color)
        self.app.image_btn.config(command=self.app.image_handler.insert_image)
        self.app.new_btn.config(command=self.app.note_manager.new_note)  # 现在不会报错
        self.app.delete_btn.config(command=self.app.note_manager.delete_note)

        # 绑定拖动窗口事件
        self.app.header.bind("<Button-1>", self.start_move)
        self.app.header.bind("<B1-Motion>", self.on_move)

    def start_move(self, event):
        self.app.offset_x = event.x
        self.app.offset_y = event.y

    def on_move(self, event):
        x = self.app.root.winfo_x() + event.x - self.app.offset_x
        y = self.app.root.winfo_y() + event.y - self.app.offset_y
        self.app.root.geometry(f"+{x}+{y}")

    def change_color(self):
        """修改顶部工具栏颜色"""
        color = colorchooser.askcolor()[1]
        if color:
            self.app.header_bg = color
            self.app.header.config(bg=color)
            self.app.color_btn.config(bg=color)
            self.app.image_btn.config(bg=color)
            self.app.pin_btn.config(bg=color if not self.app.is_pinned else "#FFD700")

    def toggle_pin(self):
        """置顶或取消置顶窗口"""
        self.app.is_pinned = not self.app.is_pinned
        self.app.root.attributes("-topmost", self.app.is_pinned)
        self.app.pin_btn.config(bg="#FFD700" if self.app.is_pinned else self.app.header_bg)

from tkinter import colorchooser

class WindowControls:
    def __init__(self, app):
        self.app = app
        self.bind_controls()

    def bind_controls(self):
        #self.app.close_btn.config(command=self.app.hide_window)
        self.app.pin_btn.config(command=self.toggle_pin)
        self.app.color_btn.config(command=self.change_color)
        self.app.image_btn.config(command=self.app.image_handler.insert_image)
        # 注意：不要在此处重新绑定 new_btn，保持其在 StickyNote.py 中的原有绑定
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
        color = colorchooser.askcolor()[1]
        if color:
            self.app.header_bg = color
            self.app.header.config(bg=color)
            # pinned color 逻辑在 _refresh_header_buttons 内部处理
            # 这里只需最后调用:
            if hasattr(self.app, "_refresh_header_buttons"):
                self.app._refresh_header_buttons()

    def toggle_pin(self):
        """置顶或取消置顶窗口，并调整按钮颜色"""
        self.app.is_pinned = not self.app.is_pinned  # 修改 StickyNote 的 is_pinned 变量
        self.app.root.attributes("-topmost", self.app.is_pinned)

        # **当 pinned 变化时，更新所有按钮颜色**
        if hasattr(self.app, "_refresh_header_buttons"):
            self.app._refresh_header_buttons()


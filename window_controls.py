from tkinter import colorchooser, Menu

class WindowControls:
    def __init__(self, app):
        self.app = app
        self.bind_controls()

    def bind_controls(self):
        # 绑定固定窗口、图片、删除按钮等
        self.app.pin_btn.config(command=self.toggle_pin)
        # 将修改颜色按钮的命令更改为打开二级菜单
        self.app.color_btn.config(command=self.open_color_menu)
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

    def open_color_menu(self):
        # 创建一个弹出菜单，用于选择修改颜色的方式
        menu = Menu(self.app.root, tearoff=0)
        menu.add_command(label="修改工具栏颜色", command=self.change_toolbar_color)
        menu.add_command(label="修改背景颜色", command=self.change_background_color)
        menu.add_command(label="修改字体颜色", command=self.change_font_color)
        menu.add_command(label="恢复默认颜色", command=self.restore_default_colors)
        # 将菜单显示在 color_btn 的下方
        x = self.app.color_btn.winfo_rootx()
        y = self.app.color_btn.winfo_rooty() + self.app.color_btn.winfo_height()
        menu.tk_popup(x, y)

    def change_toolbar_color(self):
        # 选择颜色并应用到顶部工具栏、底部工具栏、AI 切换按钮以及发送按钮
        color = colorchooser.askcolor()[1]
        if color:
            self.app.header_bg = color
            self.app.header.config(bg=color)
            if hasattr(self.app, "toolbar"):
                self.app.toolbar.config(bg=color)
            if hasattr(self.app, "ai_toggle_btn"):
                self.app.ai_toggle_btn.config(bg=color)
            if hasattr(self.app, "ai_send_button"):
                self.app.ai_send_button.config(bg=color)
            if hasattr(self.app, "_refresh_header_buttons"):
                self.app._refresh_header_buttons()

    def change_background_color(self):
        # 选择颜色并应用到主内容区背景（包括文本编辑区和 AI 聊天区的各个子区域）
        color = colorchooser.askcolor()[1]
        if color:
            self.app.text_bg = color
            self.app.content_frame.config(bg=color)
            self.app.text_widget.config(bg=color, insertbackground=self.app.text_fg)
            # 若 AI 聊天区已初始化，则更新其各部分背景色
            if hasattr(self.app, "ai_frame"):
                self.app.ai_frame.config(bg=color)
            if hasattr(self.app, "ai_chat_display"):
                self.app.ai_chat_display.config(bg=color)
            if hasattr(self.app, "ai_input_frame"):
                self.app.ai_input_frame.config(bg=color)

    def change_font_color(self):
        # 选择颜色并应用到文本控件（文本编辑区和 AI 聊天显示区）的前景色
        color = colorchooser.askcolor()[1]
        if color:
            self.app.text_fg = color
            self.app.text_widget.config(fg=color, insertbackground=color)
            if hasattr(self.app, "ai_chat_display"):
                self.app.ai_chat_display.config(fg=color)

    def restore_default_colors(self):
        # 默认颜色设置
        default_header_bg = "#3F51B5"
        default_text_bg = "#2B2B2B"
        default_text_fg = "#ECECEC"
        self.app.header_bg = default_header_bg
        self.app.text_bg = default_text_bg
        self.app.text_fg = default_text_fg
        # 恢复顶部工具栏颜色
        self.app.header.config(bg=default_header_bg)
        # 恢复底部工具栏颜色
        if hasattr(self.app, "toolbar"):
            self.app.toolbar.config(bg=default_header_bg)
        # 恢复 AI 切换按钮颜色
        if hasattr(self.app, "ai_toggle_btn"):
            self.app.ai_toggle_btn.config(bg=default_header_bg)
        # 恢复 AI 发送按钮颜色
        if hasattr(self.app, "ai_send_button"):
            self.app.ai_send_button.config(bg=default_header_bg)
        # 恢复内容区背景及文字区颜色
        self.app.content_frame.config(bg=default_text_bg)
        self.app.text_widget.config(bg=default_text_bg, fg=default_text_fg, insertbackground=default_text_fg)
        if hasattr(self.app, "ai_frame"):
            self.app.ai_frame.config(bg=default_text_bg)
        if hasattr(self.app, "ai_chat_display"):
            self.app.ai_chat_display.config(bg=default_text_bg, fg=default_text_fg)
        if hasattr(self.app, "_refresh_header_buttons"):
            self.app._refresh_header_buttons()

    def toggle_pin(self):
        """置顶或取消置顶窗口，并调整按钮颜色"""
        self.app.is_pinned = not self.app.is_pinned  # 修改 StickyNote 的 is_pinned 变量
        self.app.root.attributes("-topmost", self.app.is_pinned)
        if hasattr(self.app, "_refresh_header_buttons"):
            self.app._refresh_header_buttons()

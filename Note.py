import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
from ToolTip import ToolTip  # 悬浮提示
from AI import AIChat  # 引入 AI 模块
import time
import multiprocessing
import re
import json

global_command_queue = None
IMAGE_FOLDER = "sticky_notes_images"

def launch_sticky_note(note_id=None, command_queue=None, x=None, y=None):
    """
    允许接收 x,y 参数以指定窗口初始位置；
    若 x,y 均为 None，则使用默认 '300x400+100+100'。
    """
    global global_command_queue
    global_command_queue = command_queue
    note = StickyNote(note_id=note_id, x=x, y=y)
    note.root.mainloop()

def create_new_sticky_note():
    """只想创建默认位置的新便笺时使用"""
    p = multiprocessing.Process(target=launch_sticky_note, args=(None, global_command_queue))
    p.start()


class StickyNote:
    def __init__(self, note_id=None, master=None, x=None, y=None):
        """
        master: 可选父窗口 (通常不用)；
        x, y: 当不为 None 时，用于覆盖默认位置。
        """
        if master is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)

        self.root.title("FakeNote")
        # 如果传入 x, y，则覆盖默认位置；否则使用 "300x400+100+100"
        if x is not None and y is not None:
            geometry_str = f"300x400+{x}+{y}"
        else:
            geometry_str = "300x400+100+100"
        self.root.geometry(geometry_str)

        # 使用 grid 布局划分三个区域：顶部工具栏、内容区、底部工具栏
        self.root.grid_rowconfigure(1, weight=1)  # 内容区行可扩展
        self.root.grid_columnconfigure(0, weight=1)

        # 主背景色
        self.root.configure(bg="#1E1E1E")
        self.root.overrideredirect(False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # 便笺标识
        self.note_id = note_id or time.strftime("%Y%m%d%H%M%S", time.localtime())

        # 现代配色
        self.header_bg = "#3F51B5"
        self.text_bg = "#2B2B2B"
        self.text_fg = "#ECECEC"

        self.is_pinned = False
        self.is_ai_mode = False  # AI 模式状态

        button_fg = "#FFFFFF"
        button_font = ("Segoe UI", 11, "bold")

        # ============ 顶部工具栏 ============
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)  # 固定高度

        self.pin_btn = tk.Button(self.header, text="📌", bg=self.header_bg, fg=button_fg, bd=0, font=button_font)
        ToolTip(self.pin_btn, "固定窗口")
        self.color_btn = tk.Button(self.header, text="🎨", bg=self.header_bg, fg=button_fg, bd=0, font=button_font)
        ToolTip(self.color_btn, "更改颜色")
        self.image_btn = tk.Button(self.header, text="📷", bg=self.header_bg, fg=button_fg, bd=0, font=button_font)
        ToolTip(self.image_btn, "插入图片")
        self.list_btn = tk.Button(self.header, text="📂", bg=self.header_bg, fg=button_fg, bd=0, font=button_font,
                                  command=self.show_saved_notes_menu)
        ToolTip(self.list_btn, "查看/管理已保存便笺")
        self.new_btn = tk.Button(self.header, text="➕", bg=self.header_bg, fg=button_fg, bd=0, font=button_font,
                                 command=self.request_new_sticky_note)
        ToolTip(self.new_btn, "新建便笺")
        self.delete_btn = tk.Button(self.header, text="🗑", bg=self.header_bg, fg=button_fg, bd=0, font=button_font)
        ToolTip(self.delete_btn, "删除便笺")
        self.bold_btn = tk.Button(self.header, text="B", bg=self.header_bg, fg=button_fg, bd=0,
                                  font=("Segoe UI", 11, "bold"), command=self.toggle_bold)
        ToolTip(self.bold_btn, "加粗")
        self.italic_btn = tk.Button(self.header, text="I", bg=self.header_bg, fg=button_fg, bd=0,
                                    font=("Segoe UI", 11, "italic"), command=self.toggle_italic)
        ToolTip(self.italic_btn, "斜体")

        # 从右向左依次排列顶部按钮
        for btn in [self.pin_btn, self.color_btn, self.image_btn,
                    self.bold_btn, self.italic_btn,
                    self.list_btn, self.new_btn, self.delete_btn]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # ============ 初始化模块 ============
        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)

        # ============ 内容区域 ============
        # 使用 content_frame 作为中间区域容器，供文本编辑区和 AI 聊天区互斥显示
        self.content_frame = tk.Frame(self.root, bg=self.text_bg)
        self.content_frame.grid(row=1, column=0, sticky="nsew")

        # 创建文本编辑区（默认显示）
        self.text_widget = tk.Text(self.content_frame, wrap="word",
                                    font=("微软雅黑", 11),
                                    fg=self.text_fg, bg=self.text_bg,
                                    borderwidth=0, insertbackground="#FFFFFF",
                                    relief="flat", padx=10, pady=10)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.tag_configure("invisible", elide=True)
        self.text_widget.tag_configure("bold", font=("微软雅黑", 11, "bold"), foreground=self.text_fg)
        self.text_widget.tag_configure("italic", font=("微软雅黑", 11, "italic"), foreground=self.text_fg)
        self.text_widget.tag_configure("bold_italic", font=("微软雅黑", 11, "bold", "italic"), foreground=self.text_fg)
        self.shortcut_manager = TextShortcuts(self.text_widget, image_handler=self.image_handler)
        self.note_manager.load_note()
        self.notes_menu = None

        # ============ AI 聊天区域（默认隐藏） ============
        self.ai_frame = tk.Frame(self.content_frame, bg=self.text_bg)
        self.ai_chat_display = tk.Text(self.ai_frame, wrap="word", height=10,
                                       font=("微软雅黑", 10), fg=self.text_fg,
                                       bg=self.text_bg, borderwidth=0)
        self.ai_chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.ai_chat_display.insert(tk.END, "🤖 AI 助手已加载，输入问题开始对话...\n")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_input_frame = tk.Frame(self.ai_frame, bg=self.text_bg)
        self.ai_input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.ai_input_entry = tk.Entry(self.ai_input_frame, font=("微软雅黑", 10),
                                       fg=self.text_fg, bg=self.text_bg, insertbackground="#FFFFFF")
        self.ai_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.ai_input_entry.bind("<Return>", self.send_message)
        self.ai_send_button = tk.Button(self.ai_input_frame, text="发送",
                                        command=self.send_message, bg=self.header_bg, fg="white")
        self.ai_send_button.pack(side=tk.RIGHT)
        self.ai_chat = AIChat()

        # ============ 底部工具栏 ============
        self.toolbar = tk.Frame(self.root, bg=self.header_bg, height=30)
        self.toolbar.grid(row=2, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)  # 固定高度
        # 底部工具栏样式与顶部工具栏一致，添加 AI 切换按钮仅显示图标 🤖
        self.ai_toggle_btn = tk.Button(self.toolbar, text="🤖", command=self.toggle_ai_mode,
                                       bg=self.header_bg, fg="white", font=button_font, relief="flat", bd=0)
        self.ai_toggle_btn.pack(side=tk.LEFT, padx=10, pady=3)

        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, self._ensure_topmost_state)

    def _darken_color(self, hexcolor, factor=0.7):
        """返回加深后的颜色字符串，与 pinned 按钮逻辑一致"""
        hexcolor = hexcolor.lstrip('#')
        r = int(hexcolor[0:2], 16)
        g = int(hexcolor[2:4], 16)
        b = int(hexcolor[4:6], 16)
        import colorsys
        (h, s, v) = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        v = v * factor
        (r2, g2, b2) = colorsys.hsv_to_rgb(h, s, v)
        r2 = int(r2 * 255)
        g2 = int(g2 * 255)
        b2 = int(b2 * 255)
        return f"#{r2:02x}{g2:02x}{b2:02x}"

    def toggle_ai_mode(self):
        """切换 AI 模式（仅切换内容区域显示），并更新 AI 按钮背景颜色，逻辑与固定窗口按钮一致"""
        self.is_ai_mode = not self.is_ai_mode
        if self.is_ai_mode:
            self.text_widget.pack_forget()
            self.ai_frame.pack(fill=tk.BOTH, expand=True)
            self.ai_toggle_btn.config(bg=self._darken_color(self.header_bg, 0.7))
        else:
            self.ai_frame.pack_forget()
            self.text_widget.pack(fill=tk.BOTH, expand=True)
            self.ai_toggle_btn.config(bg=self.header_bg)

    def send_message(self, event=None):
        user_message = self.ai_input_entry.get().strip()
        if not user_message:
            return
        self.ai_input_entry.delete(0, tk.END)
        self.ai_chat_display.config(state=tk.NORMAL)
        self.ai_chat_display.insert(tk.END, f"🧑 你: {user_message}\n", "user")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_chat_display.config(state=tk.NORMAL)
        self.ai_chat_display.insert(tk.END, "🤖 AI: 正在思考...\n", "ai")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_chat.get_response(user_message, self.display_response)

    def display_response(self, ai_response):
        """更新 AI 对话框"""
        self.root.after(0, self._update_chat_display, ai_response)

    def _update_chat_display(self, ai_response):
        self.ai_chat_display.config(state=tk.NORMAL)
        self.ai_chat_display.insert(tk.END, f"🤖 AI: {ai_response}\n\n", "ai")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_chat_display.see(tk.END)

    def hide_window(self):
        self.note_manager.save_note()
        self.root.destroy()

    def _ensure_topmost_state(self):
        """如果没有固定，则关闭 topmost；否则保持"""
        if not self.is_pinned:
            self.root.attributes("-topmost", False)
        else:
            self.root.attributes("-topmost", True)

    def _refresh_header_buttons(self):
        """
        当 header_bg 改变后，刷新所有标题栏按钮的背景；
        若窗口被固定，则加深 pin 按钮的背景色。
        """
        def _darken_color(hexcolor, factor=0.7):
            hexcolor = hexcolor.lstrip('#')
            r = int(hexcolor[0:2], 16)
            g = int(hexcolor[2:4], 16)
            b = int(hexcolor[4:6], 16)
            import colorsys
            (h, s, v) = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            v = v * factor
            (r2, g2, b2) = colorsys.hsv_to_rgb(h, s, v)
            r2 = int(r2 * 255)
            g2 = int(g2 * 255)
            b2 = int(b2 * 255)
            return f"#{r2:02x}{g2:02x}{b2:02x}"
        all_buttons = [self.pin_btn, self.color_btn, self.image_btn,
                       self.bold_btn, self.italic_btn,
                       self.list_btn, self.new_btn, self.delete_btn]
        for b in all_buttons:
            b.config(bg=self.header_bg)
        if self.is_pinned:
            dark_bg = _darken_color(self.header_bg, 0.7)
            self.pin_btn.config(bg=dark_bg)

    def request_new_sticky_note(self):
        global global_command_queue
        if global_command_queue is not None:
            import re
            geo_str = self.root.geometry()
            match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geo_str)
            if match:
                width  = int(match.group(1))
                height = int(match.group(2))
                old_x  = int(match.group(3))
                old_y  = int(match.group(4))
            else:
                old_x, old_y = 100, 100
                width = 300
            new_x = old_x + width + 30
            new_y = old_y
            global_command_queue.put(("new_with_xy", new_x, new_y))

    def minimize_window(self):
        self.root.withdraw()

    def show_saved_notes_menu(self, event=None):
        from note_manager import NoteManager, SAVE_FILE
        import tkinter.simpledialog as simpledialog
        from tkinter import messagebox
        data = NoteManager.load_notes_list()
        if hasattr(self, "notes_menu") and self.notes_menu:
            self.notes_menu.destroy()
        self.notes_menu = tk.Menu(self.root, tearoff=0,
                                  bg="#3E3E3E", fg="#FFFFFF",
                                  activebackground="#FFCC00", activeforeground="black")
        if not data:
            self.notes_menu.add_command(label="暂无便笺", state="disabled")
        else:
            for note_id in sorted(data.keys()):
                note_info = data[note_id]
                display_label = note_info.get("name", note_id)
                sub_menu = tk.Menu(self.root, tearoff=0,
                                   bg="#3E3E3E", fg="#FFFFFF",
                                   activebackground="#FFCC00", activeforeground="black")
                def open_note(nid=note_id):
                    import re
                    geo_str2 = self.root.geometry()
                    m2 = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geo_str2)
                    if m2:
                        w2 = int(m2.group(1))
                        h2 = int(m2.group(2))
                        ox2 = int(m2.group(3))
                        oy2 = int(m2.group(4))
                    else:
                        ox2, oy2 = 100, 100
                        w2 = 300
                    new_x2 = ox2 + w2 + 30
                    new_y2 = oy2
                    global global_command_queue
                    if global_command_queue:
                        global_command_queue.put(("open_with_xy", nid, new_x2, new_y2))
                def rename_note(nid=note_id):
                    current_name = data[nid].get("name", nid)
                    new_name = simpledialog.askstring("重命名", "请输入新的便笺名称：",
                                                      parent=self.root, initialvalue=current_name)
                    if new_name:
                        data[nid]["name"] = new_name
                        with open(SAVE_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        self.show_saved_notes_menu()
                def delete_note(nid=note_id):
                    if messagebox.askyesno("删除便笺", "确定删除此便笺吗？", parent=self.root):
                        if nid in data:
                            del data[nid]
                            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)
                        self.show_saved_notes_menu()
                sub_menu.add_command(label="打开", command=open_note)
                sub_menu.add_command(label="重命名", command=rename_note)
                sub_menu.add_command(label="删除", command=delete_note)
                self.notes_menu.add_cascade(label=display_label, menu=sub_menu)
        bx = self.list_btn.winfo_rootx()
        by = self.list_btn.winfo_rooty() + self.list_btn.winfo_height()
        self.notes_menu.tk_popup(bx, by)

    def toggle_bold(self):
        try:
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
        except tk.TclError:
            return
        has_bold = self._has_tag_in_range("bold", start, end)
        has_italic = self._has_tag_in_range("italic", start, end)
        has_bi = self._has_tag_in_range("bold_italic", start, end)
        self.text_widget.tag_remove("bold", start, end)
        self.text_widget.tag_remove("italic", start, end)
        self.text_widget.tag_remove("bold_italic", start, end)
        if has_bi:
            if not has_italic:
                self.text_widget.tag_add("italic", start, end)
        elif has_bold:
            pass
        elif has_italic:
            self.text_widget.tag_add("bold_italic", start, end)
        else:
            self.text_widget.tag_add("bold", start, end)

    def toggle_italic(self):
        try:
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
        except tk.TclError:
            return
        has_bold = self._has_tag_in_range("bold", start, end)
        has_italic = self._has_tag_in_range("italic", start, end)
        has_bi = self._has_tag_in_range("bold_italic", start, end)
        self.text_widget.tag_remove("bold", start, end)
        self.text_widget.tag_remove("italic", start, end)
        self.text_widget.tag_remove("bold_italic", start, end)
        if has_bi:
            if not has_bold:
                self.text_widget.tag_add("bold", start, end)
        elif has_italic:
            pass
        elif has_bold:
            self.text_widget.tag_add("bold_italic", start, end)
        else:
            self.text_widget.tag_add("italic", start, end)

    def _has_tag_in_range(self, tag_name, start, end):
        ranges = self.text_widget.tag_ranges(tag_name)
        for i in range(0, len(ranges), 2):
            tag_start = ranges[i]
            tag_end = ranges[i + 1]
            if (self.text_widget.compare(tag_start, "<=", start) and
                    self.text_widget.compare(tag_end, ">=", end)):
                return True
        return False

    def load_content(self, content):
        self.text_widget.delete("1.0", tk.END)
        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                self.text_widget.insert(tk.END, part)
            else:
                try:
                    from PIL import Image
                    image = Image.open(part)
                    self.image_handler.insert_pil_image(image, part, add_newline=False)
                except Exception:
                    self.text_widget.insert(tk.END, f"[图片加载失败:{part}]")

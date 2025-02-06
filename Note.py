#版权声明
#本项目受 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 许可协议保护。

import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
from ToolTip import ToolTip  # 悬浮提示
from AI import AIChat, load_config, save_config  # 引入 AI 模块及配置函数
import time
import multiprocessing
import re
import json
import os  # 用于文件操作

global_command_queue = None
IMAGE_FOLDER = "sticky_notes_images"


def launch_sticky_note(note_id=None, command_queue=None, x=None, y=None):
    global global_command_queue
    global_command_queue = command_queue
    note = StickyNote(note_id=note_id, x=x, y=y)
    note.root.mainloop()


def create_new_sticky_note():
    p = multiprocessing.Process(target=launch_sticky_note, args=(None, global_command_queue))
    p.start()


class StickyNote:
    def __init__(self, note_id=None, master=None, x=None, y=None):
        if master is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)
        self.root.title("FakeNote")
        #self.root.iconbitmap("FakeNote.ico")  # 需要使用 Logo 时启用
        if x is not None and y is not None:
            geometry_str = f"300x400+{x}+{y}"
        else:
            geometry_str = "300x400+100+100"
        self.root.geometry(geometry_str)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.configure(bg="#1E1E1E")
        self.root.overrideredirect(False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.note_id = note_id or time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.header_bg = "#3F51B5"
        self.text_bg = "#2B2B2B"
        self.text_fg = "#ECECEC"
        self.is_pinned = False
        self.is_ai_mode = False
        button_fg = "#FFFFFF"
        button_font = ("Segoe UI", 11, "bold")
        # 顶部工具栏
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)
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
        for btn in [self.pin_btn, self.color_btn, self.image_btn,
                    self.bold_btn, self.italic_btn,
                    self.list_btn, self.new_btn, self.delete_btn]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)
        # 初始化模块
        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)
        # 内容区域
        self.content_frame = tk.Frame(self.root, bg=self.text_bg)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
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
        # AI 聊天区域（默认隐藏）
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
        # 底部工具栏
        self.toolbar = tk.Frame(self.root, bg=self.header_bg, height=30)
        self.toolbar.grid(row=2, column=0, sticky="ew")
        self.toolbar.grid_propagate(False)
        # 将 AI 切换按钮移动到底部工具栏最右侧
        self.ai_toggle_btn = tk.Button(self.toolbar, text="🤖", command=self.toggle_ai_mode,
                                       bg=self.header_bg, fg="white", font=button_font,
                                       relief="flat", bd=0)
        self.ai_toggle_btn.pack(side=tk.RIGHT, padx=10, pady=3)
        ToolTip(self.ai_toggle_btn, "AI聊天")
        # 右键弹出设置菜单，用于配置 AI 参数、prompt 多套设置及使用说明
        self.root.bind("<Button-3>", self.show_context_menu)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, self._ensure_topmost_state)

    def _darken_color(self, hexcolor, factor=0.7):
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
        self.ai_chat_display.insert(tk.END, f"🧑 我: {user_message}\n", "user")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_chat_display.config(state=tk.NORMAL)
        self.ai_chat_display.insert(tk.END, "🤖 AI: 正在思考...\n", "ai")
        self.ai_chat_display.config(state=tk.DISABLED)
        self.ai_chat.get_response(user_message, self.display_response)

    def display_response(self, ai_response):
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
        if not self.is_pinned:
            self.root.attributes("-topmost", False)
        else:
            self.root.attributes("-topmost", True)

    def _refresh_header_buttons(self):
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
                width = int(match.group(1))
                height = int(match.group(2))
                old_x = int(match.group(3))
                old_y = int(match.group(4))
            else:
                old_x, old_y = 100, 100
                width = 300
            new_x = old_x + 30
            new_y = old_y + 30
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
                    new_x2 = ox2 + 30
                    new_y2 = oy2 + 30
                    global global_command_queue
                    if global_command_queue:
                        global_command_queue.put(("open_with_xy", nid, new_x2, new_y2))

                def rename_note(nid=note_id):
                    current_name = data[note_id].get("name", note_id)
                    new_name = simpledialog.askstring("重命名", "请输入新的便笺名称：",
                                                      parent=self.root, initialvalue=current_name)
                    if new_name:
                        data[note_id]["name"] = new_name
                        with open(SAVE_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        self.show_saved_notes_menu()

                def delete_note(nid=note_id):
                    from tkinter import messagebox
                    if messagebox.askyesno("删除便笺", "确定删除此便笺吗？", parent=self.root):
                        if note_id in data:
                            del data[note_id]
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

    def _has_tag_in_range(self, tag_name, start, end):
        ranges = self.text_widget.tag_ranges(tag_name)
        for i in range(0, len(ranges), 2):
            tag_start = ranges[i]
            tag_end = ranges[i + 1]
            if (self.text_widget.compare(tag_start, "<=", start) and
                    self.text_widget.compare(tag_end, ">=", end)):
                return True
        return False

    def show_context_menu(self, event):
        """右键弹出菜单，包含 AI 设置和使用说明两个选项"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="AI 设置", command=self.open_ai_settings)
        menu.add_command(label="使用说明", command=self.show_usage)
        menu.tk_popup(event.x_root, event.y_root)

    # 新增：显示使用说明窗口
    def show_usage(self):
        """
        显示使用说明窗口，展示 usage.txt 文件的内容。
        如果内容中包含图片标记 [[IMG:xxx]]，则从 Media Files 目录加载图片。
        """
        USAGE_FILE = "usage.txt"
        USAGE_IMAGE_FOLDER = "Media Files"  # 修改为新的目录

        usage_win = tk.Toplevel(self.root)
        usage_win.title("使用说明")
        usage_win.geometry("325x400+100+100")
        usage_win.configure(bg=self.text_bg)

        # 创建只读文本区域
        usage_text = tk.Text(usage_win, wrap="word", bg=self.text_bg, fg=self.text_fg,
                             font=("微软雅黑", 11), state="disabled")
        usage_text.pack(fill=tk.BOTH, expand=True)

        # 如果文件不存在，则新建一个并写入默认提示内容
        if not os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                f.write("请在此处编写使用说明，支持图片插入，例如 [[IMG:example.png]]")

        # 读取文件内容
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析文本内容并插入图片
        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)

        usage_text.config(state="normal")
        usage_text.delete("1.0", tk.END)
        usage_text.image_refs = []  # 保存图片引用，防止被垃圾回收

        for i, part in enumerate(parts):
            if i % 2 == 0:
                usage_text.insert(tk.END, part)
            else:
                img_path = part.strip().replace("\\", "/")

                # 确保图片路径正确，优先查找 Media Files 目录
                if "/" not in img_path and os.sep not in img_path:
                    img_path = os.path.join(USAGE_IMAGE_FOLDER, img_path)
                img_path = os.path.normpath(img_path)

                base_dir = os.path.dirname(os.path.abspath(__file__))
                if not os.path.isabs(img_path):
                    img_full_path = os.path.join(base_dir, img_path)
                else:
                    img_full_path = img_path

                if not os.path.exists(img_full_path):
                    usage_text.insert(tk.END, f"[图片加载失败: {img_path}]\n")
                    continue

                try:
                    from PIL import Image, ImageTk
                    image = Image.open(img_full_path)
                    max_width = 300
                    if image.width > max_width:
                        ratio = max_width / image.width
                        new_size = (max_width, int(image.height * ratio))
                        image = image.resize(new_size, Image.LANCZOS)

                    photo = ImageTk.PhotoImage(image)
                    usage_text.image_create(tk.END, image=photo)
                    usage_text.insert(tk.END, "\n")
                    usage_text.image_refs.append(photo)  # 保存图片引用，防止被垃圾回收
                except Exception as e:
                    usage_text.insert(tk.END, f"[图片加载失败: {img_path}]\n")

        usage_text.config(state="disabled")

    def open_ai_settings(self):
        """打开 AI 设置对话框，配置 API、模型以及多套 prompt（system 和 user 部分）。
        下拉列表中固定显示“聊天”和“新建模板”，后续追加其它模板；
        当点击模板时，显示二级子菜单【应用】、【重命名】、【删除】选项，
        其中默认模板“聊天”的 prompt 为空且禁止修改；
        如果用户点击只读的编辑框，则自动转到“新建模板”；
        保存时如果选择“新建模板”，则弹出对话框要求输入模板名称，否则直接覆盖保存当前模板内容。
        同时新增“Model”填写框，其值保存到配置文件和 .env 文件。"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("AI 设置")
        settings_win.geometry("530x280")
        settings_win.transient(self.root)
        settings_win.grab_set()
        settings_win.configure(bg=self.text_bg)

        label_font = ("微软雅黑", 11)
        entry_font = ("微软雅黑", 11)
        btn_font = ("Segoe UI", 11, "bold")
        label_fg = self.text_fg
        entry_bg = self.text_bg
        entry_fg = self.text_fg

        config = load_config()

        tk.Label(settings_win, text="API URL:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=0, column=0, padx=10, pady=5, sticky="e")
        api_url_var = tk.StringVar(value=config.get("api_url", ""))
        tk.Entry(settings_win, textvariable=api_url_var, width=40, font=entry_font,
                 bg=entry_bg, fg=entry_fg, insertbackground=entry_fg) \
            .grid(row=0, column=1, padx=10, pady=5)

        tk.Label(settings_win, text="API Key:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=1, column=0, padx=10, pady=5, sticky="e")
        api_key_var = tk.StringVar(value=config.get("api_key", ""))
        tk.Entry(settings_win, textvariable=api_key_var, width=40, font=entry_font,
                 bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, show="*") \
            .grid(row=1, column=1, padx=10, pady=5)

        tk.Label(settings_win, text="Model:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=2, column=0, padx=10, pady=5, sticky="e")
        model_var = tk.StringVar(value=config.get("model", ""))
        tk.Entry(settings_win, textvariable=model_var, width=40, font=entry_font,
                 bg=entry_bg, fg=entry_fg, insertbackground=entry_fg) \
            .grid(row=2, column=1, padx=10, pady=5)

        # 处理 prompt 配置
        prompts_dict = config.get("prompts", {})
        if "聊天" not in prompts_dict:
            prompts_dict["聊天"] = {"system": "", "user": ""}
        other_prompts = sorted([name for name in prompts_dict.keys() if name != "聊天"])
        prompt_names = ["聊天", "新建模板"] + other_prompts

        active_prompt_initial = config.get("active_prompt", "聊天")
        if active_prompt_initial not in prompt_names:
            active_prompt_initial = "聊天"
        active_prompt_var = tk.StringVar(value=active_prompt_initial)

        tk.Label(settings_win, text="选择已有Prompt:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=3, column=0, padx=10, pady=5, sticky="e")
        menubtn = tk.Menubutton(settings_win, textvariable=active_prompt_var, relief="raised", width=30,
                                font=entry_font, bg=self.header_bg, fg=label_fg)
        menubtn.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        menu = tk.Menu(menubtn, tearoff=0, bg=self.header_bg, fg=label_fg, font=entry_font)
        menubtn.config(menu=menu)

        def create_template_submenu(name):
            sub_menu = tk.Menu(menu, tearoff=0, bg=self.header_bg, fg=label_fg, font=entry_font)

            def apply_template():
                active_prompt_var.set(name)
                if name == "聊天":
                    system_var.set("")
                    user_var.set("")
                    system_entry.config(state="disabled", disabledbackground=entry_bg)
                    user_entry.config(state="disabled", disabledbackground=entry_bg)
                else:
                    system_entry.config(state="normal")
                    user_entry.config(state="normal")
                    system_val = prompts_dict.get(name, {}).get("system", "")
                    user_val = prompts_dict.get(name, {}).get("user", "")
                    system_var.set(system_val)
                    user_var.set(user_val)

            def rename_template():
                from tkinter import simpledialog, messagebox
                if name in ["聊天", "新建模板"]:
                    messagebox.showerror("错误", "默认模板不能重命名！", parent=settings_win)
                    return
                new_name = simpledialog.askstring("重命名模板", "请输入新的模板名称：", parent=settings_win)
                if new_name:
                    new_name = new_name.strip()
                    if new_name in prompts_dict and new_name != name:
                        messagebox.showerror("错误", "该模板名称已存在！", parent=settings_win)
                        return
                    prompts_dict[new_name] = prompts_dict.pop(name)
                    active_prompt_var.set(new_name)
                    rebuild_menu()
                    messagebox.showinfo("重命名成功", f"模板已重命名为 '{new_name}'", parent=settings_win)

            def delete_template():
                from tkinter import messagebox
                if name in ["聊天", "新建模板"]:
                    messagebox.showerror("错误", "默认模板不能删除！", parent=settings_win)
                    return
                if messagebox.askyesno("删除模板", f"确定删除模板 '{name}'？", parent=settings_win):
                    prompts_dict.pop(name, None)
                    rebuild_menu()
                    active_prompt_var.set("聊天")
                    messagebox.showinfo("删除成功", f"模板 '{name}' 已删除。", parent=settings_win)

            sub_menu.add_command(label="应用", command=apply_template)
            sub_menu.add_command(label="重命名", command=rename_template)
            sub_menu.add_command(label="删除", command=delete_template)
            return sub_menu

        def rebuild_menu():
            menu.delete(0, "end")
            for fixed in ["聊天", "新建模板"]:
                menu.add_command(label=fixed, command=lambda n=fixed: active_prompt_var.set(n))
            others = sorted([name for name in prompts_dict.keys() if name not in ["聊天"]])
            for name in others:
                menu.add_cascade(label=name, menu=create_template_submenu(name))

        rebuild_menu()

        def on_prompt_select(*args):
            name = active_prompt_var.get()
            if name == "聊天":
                system_var.set("")
                user_var.set("")
                system_entry.config(state="disabled", disabledbackground=entry_bg)
                user_entry.config(state="disabled", disabledbackground=entry_bg)
            else:
                system_entry.config(state="normal")
                user_entry.config(state="normal")
                system_val = prompts_dict.get(name, {}).get("system", "")
                user_val = prompts_dict.get(name, {}).get("user", "")
                system_var.set(system_val)
                user_var.set(user_val)

        active_prompt_var.trace("w", on_prompt_select)

        tk.Label(settings_win, text="System Prompt:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=4, column=0, padx=10, pady=5, sticky="e")
        system_var = tk.StringVar(value=prompts_dict.get(active_prompt_var.get(), {}).get("system", ""))
        system_entry = tk.Entry(settings_win, textvariable=system_var, width=40, font=entry_font,
                                bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        system_entry.grid(row=4, column=1, padx=10, pady=5)
        tk.Label(settings_win, text="User Prompt:", font=label_font, bg=self.text_bg, fg=label_fg) \
            .grid(row=5, column=0, padx=10, pady=5, sticky="e")
        user_var = tk.StringVar(value=prompts_dict.get(active_prompt_var.get(), {}).get("user", ""))
        user_entry = tk.Entry(settings_win, textvariable=user_var, width=40, font=entry_font,
                              bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        user_entry.grid(row=5, column=1, padx=10, pady=5)

        def switch_to_new(event):
            if active_prompt_var.get() == "聊天":
                active_prompt_var.set("新建模板")
                system_entry.config(state="normal")
                user_entry.config(state="normal")

        system_entry.bind("<Button-1>", switch_to_new)
        user_entry.bind("<Button-1>", switch_to_new)

        def save_settings():
            new_config = {
                "api_url": api_url_var.get().strip(),
                "api_key": api_key_var.get().strip(),
                "model": model_var.get().strip(),
                "prompts": prompts_dict
            }
            chosen_prompt = active_prompt_var.get().strip()
            new_system = system_var.get().strip()
            new_user = user_var.get().strip()
            from tkinter import simpledialog, messagebox
            if chosen_prompt == "新建模板" or not chosen_prompt:
                new_name = simpledialog.askstring("保存模板", "请输入保存的 Prompt 模板名称：", parent=settings_win)
                if not new_name:
                    messagebox.showerror("错误", "模板名称不能为空！", parent=settings_win)
                    return
                chosen_prompt = new_name.strip()
            if chosen_prompt == "聊天":
                new_system = ""
                new_user = ""
            new_config["prompts"][chosen_prompt] = {"system": new_system, "user": new_user}
            new_config["active_prompt"] = chosen_prompt
            save_config(new_config)
            self.ai_chat.update_config(new_config)
            settings_win.destroy()

        tk.Button(settings_win, text="保存", font=btn_font, command=save_settings,
                  bg=self.header_bg, fg=label_fg) \
            .grid(row=7, column=0, columnspan=3, pady=15)

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


if __name__ == "__main__":
    root = tk.Tk()
    app = StickyNote(master=root)
    root.mainloop()

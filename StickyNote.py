import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
import time
import multiprocessing
import re

# 全局命令队列（用于多进程间通知新建便笺）
global_command_queue = None

class StickyNote:
    def __init__(self, note_id=None, master=None):
        """
        如果 master 为 None，则在独立进程中创建自己的 Tk() 主窗口；
        否则在传入的 master 上创建 Toplevel 窗口。
        """
        if master is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)
        self.root.title("便笺")
        self.root.geometry("300x400+100+100")
        self.root.configure(bg="#2B2B2B")
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # 默认使用当前时间（格式：YYYYMMDDHHMMSS）作为便笺标识
        self.note_id = note_id or time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.header_bg = "#FFCC00"
        self.text_bg = "#3E3E3E"
        self.text_fg = "#FFFFFF"
        self.is_pinned = False

        # 创建标题栏
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.pack(fill=tk.X, side=tk.TOP)

        # 创建各个按钮
        self.close_btn = tk.Button(self.header, text="✖", bg="red", fg="white", bd=0, padx=5,
                                   font=("Arial", 12, "bold"), command=self.hide_window)
        self.min_btn = tk.Button(self.header, text="🗕", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12), command=self.minimize_window)
        self.pin_btn = tk.Button(self.header, text="📌", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12))
        self.color_btn = tk.Button(self.header, text="🎨", bg=self.header_bg, fg="black", bd=0,
                                   font=("Arial", 12))
        self.image_btn = tk.Button(self.header, text="📷", bg=self.header_bg, fg="black", bd=0,
                                   font=("Arial", 12))
        # 📂 按钮：点击后显示所有已保存的便笺
        self.list_btn = tk.Button(self.header, text="📂", bg=self.header_bg, fg="black", bd=0,
                                  font=("Arial", 12), command=self.show_saved_notes)
        # ➕ 按钮：点击后通过全局命令队列通知主进程新建便笺
        self.new_btn = tk.Button(self.header, text="➕", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12), command=self.request_new_sticky_note)
        self.delete_btn = tk.Button(self.header, text="🗑", bg=self.header_bg, fg="black", bd=0,
                                    font=("Arial", 12))

        for btn in [self.close_btn, self.min_btn, self.pin_btn, self.color_btn,
                    self.image_btn, self.list_btn, self.new_btn, self.delete_btn]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 初始化各模块
        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)

        # 仅创建一个文本编辑区域
        self.text_widget = tk.Text(self.root, wrap="word", font=("Arial", 14),
                                   fg=self.text_fg, bg=self.text_bg,
                                   borderwidth=0, insertbackground="white",
                                   relief="flat", padx=10, pady=10)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        # 配置一个隐藏文本的标签（需要 Tk 8.6 及以上支持）
        self.text_widget.tag_configure("invisible", elide=True)

        self.shortcut_manager = TextShortcuts(self.text_widget)
        self.root.bind("<Control-v>", self.image_handler.paste)

        # 加载该便笺的内容（包括图片标记，加载后会自动恢复图片）
        self.note_manager.load_note()

    def load_content(self, content):
        """
        根据保存的文本内容加载便笺，
        当内容中存在图片标记（格式 [[IMG:<图片路径>]]）时，自动读取并插入图片。
        """
        self.text_widget.delete("1.0", tk.END)
        # 使用正则表达式拆分文本，奇数项为图片路径
        pattern = r"\[\[IMG:(.*?)\]\]"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                self.text_widget.insert(tk.END, part)
            else:
                try:
                    from PIL import Image
                    image = Image.open(part)
                    # 调用时将 add_newline 设为 False，避免重复换行
                    self.image_handler.insert_pil_image(image, part, add_newline=False)
                except Exception as e:
                    self.text_widget.insert(tk.END, f"[图片加载失败:{part}]")

    def hide_window(self):
        """窗口关闭时自动保存内容（仅当内容不为空时），然后关闭窗口"""
        self.note_manager.save_note()
        self.root.destroy()

    def minimize_window(self):
        self.root.withdraw()

    def request_new_sticky_note(self):
        global global_command_queue
        if global_command_queue is not None:
            global_command_queue.put("new")

    def show_saved_notes(self):
        """点击📂按钮后，弹出窗口显示所有已保存便笺，支持重命名（修改原始名称）和删除。
        若便笺已重命名，则列表中只显示重命名后的名称，不显示原始时间信息。"""
        from note_manager import NoteManager, SAVE_FILE
        data = NoteManager.load_notes_list()

        win = tk.Toplevel(self.root)
        win.title("已保存便笺")
        win.geometry("500x350")
        win.configure(bg="#2B2B2B")

        # 标题标签
        header_label = tk.Label(win, text="已保存便笺", font=("Helvetica", 16, "bold"),
                                fg="#FFCC00", bg="#2B2B2B")
        header_label.pack(pady=(10, 5))

        # 容器 Frame 用于放置 Listbox 与滚动条
        list_frame = tk.Frame(win, bg="#2B2B2B")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        listbox = tk.Listbox(list_frame, bg="#3E3E3E", fg="#FFFFFF",
                             font=("Helvetica", 12), selectbackground="#FFCC00",
                             activestyle="none", bd=0, highlightthickness=0)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        # 定义一个列表保存每个记录对应的原始键（时间标识）
        notes_keys = []

        def refresh_list():
            nonlocal notes_keys
            notes_keys = []
            listbox.delete(0, tk.END)
            data = NoteManager.load_notes_list()
            for key in sorted(data.keys()):
                note = data[key]
                # 预览文本：去除换行并取前30字符
                content = note["text"].strip().replace("\n", " ")
                preview = content[:30] + ("..." if len(content) > 30 else "")
                # 如果已重命名，则仅显示新名称；否则显示原始标识（时间）
                if "name" in note:
                    display_label = note["name"]
                else:
                    display_label = key
                notes_keys.append(key)
                listbox.insert(tk.END, f"{display_label}: {preview}")

        refresh_list()

        # 双击列表项时打开对应便笺窗口
        def open_note(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                note_id = notes_keys[index]
                p = multiprocessing.Process(target=launch_sticky_note, args=(note_id, global_command_queue))
                p.start()

        listbox.bind("<Double-Button-1>", open_note)

        # 重命名功能：修改原始名称（时间），更新后列表中仅显示新名称
        def rename_note():
            import tkinter.simpledialog as simpledialog
            selection = listbox.curselection()
            if not selection:
                return
            index = selection[0]
            note_id = notes_keys[index]
            data = NoteManager.load_notes_list()
            # 使用原始标识作为初始值（或当前名称，如果已存在）
            current_name = data[note_id].get("name", note_id)
            new_name = simpledialog.askstring("重命名", "请输入新的便笺名称：",
                                              parent=win, initialvalue=current_name)
            if new_name:
                if note_id in data:
                    data[note_id]["name"] = new_name
                    import json
                    with open(SAVE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    refresh_list()

        # 删除功能：确认删除后更新 JSON 并刷新列表显示
        def delete_note():
            from tkinter import messagebox
            selection = listbox.curselection()
            if not selection:
                return
            index = selection[0]
            note_id = notes_keys[index]
            if messagebox.askyesno("删除便笺", "确定删除此便笺吗？", parent=win):
                data = NoteManager.load_notes_list()
                if note_id in data:
                    del data[note_id]
                    import json
                    with open(SAVE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    refresh_list()

        # 按钮区域
        btn_frame = tk.Frame(win, bg="#2B2B2B")
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        rename_btn = tk.Button(btn_frame, text="重命名", font=("Helvetica", 12),
                               bg="#FFCC00", fg="black", command=rename_note)
        rename_btn.pack(side=tk.LEFT, padx=10)

        delete_btn = tk.Button(btn_frame, text="删除", font=("Helvetica", 12),
                               bg="#FFCC00", fg="black", command=delete_note)
        delete_btn.pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(btn_frame, text="关闭", font=("Helvetica", 12),
                              bg="#FFCC00", fg="black", command=win.destroy)
        close_btn.pack(side=tk.RIGHT, padx=10)


def launch_sticky_note(note_id=None, command_queue=None):
    global global_command_queue
    global_command_queue = command_queue
    note = StickyNote(note_id=note_id)
    note.root.mainloop()

def create_new_sticky_note():
    p = multiprocessing.Process(target=launch_sticky_note, args=(None, global_command_queue))
    p.start()

if __name__ == "__main__":
    launch_sticky_note()

import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
import time
import multiprocessing
import re
import json

# 全局命令队列（用于多进程间通知新建便笺）
global_command_queue = None
IMAGE_FOLDER = "sticky_notes_images"


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
        # 使用标准窗口 (False)，让操作系统提供原生最小化、关闭按钮
        self.root.overrideredirect(False)
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

        # 创建各个按钮（去掉 🗕 和 ✖；保留 📌、🎨、📷、📂、➕、🗑）
        self.pin_btn = tk.Button(
            self.header, text="📌", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12)
        )
        self.color_btn = tk.Button(
            self.header, text="🎨", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12)
        )
        self.image_btn = tk.Button(
            self.header, text="📷", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12)
        )
        # 📂 按钮：点击后弹出菜单，下拉显示所有已保存便笺
        self.list_btn = tk.Button(
            self.header, text="📂", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12), command=self.show_saved_notes_menu
        )
        # ➕ 按钮：点击后通过全局命令队列通知主进程新建便笺
        self.new_btn = tk.Button(
            self.header, text="➕", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12), command=self.request_new_sticky_note
        )
        self.delete_btn = tk.Button(
            self.header, text="🗑", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12)
        )

        # ============ 新增 “B” 加粗 和 “I” 斜体按钮 ============
        self.bold_btn = tk.Button(
            self.header, text="B", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12, "bold"), command=self.toggle_bold
        )
        self.italic_btn = tk.Button(
            self.header, text="I", bg=self.header_bg, fg="black", bd=0,
            font=("Arial", 12, "italic"), command=self.toggle_italic
        )

        # 将所有按钮按顺序 pack 到标题栏
        for btn in [
            self.pin_btn, self.color_btn, self.image_btn,
            self.bold_btn, self.italic_btn,  # 新增加粗、斜体
            self.list_btn, self.new_btn, self.delete_btn
        ]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 初始化各模块
        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)

        # 创建一个文本编辑区域
        self.text_widget = tk.Text(
            self.root, wrap="word", font=("Arial", 14),
            fg=self.text_fg, bg=self.text_bg,
            borderwidth=0, insertbackground="white",
            relief="flat", padx=10, pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        # 隐藏文本标签（需要 Tk 8.6+ 支持）
        self.text_widget.tag_configure("invisible", elide=True)

        # ========== 配置加粗 / 斜体的文本标签 ==========
        self.text_widget.tag_configure("bold", font=("Arial", 14, "bold"), foreground=self.text_fg)
        self.text_widget.tag_configure("italic", font=("Arial", 14, "italic"), foreground=self.text_fg)

        # 绑定快捷键管理器，并将 image_handler 传入
        self.shortcut_manager = TextShortcuts(self.text_widget, image_handler=self.image_handler)

        # 加载便笺内容（包括图片标记）
        self.note_manager.load_note()

        # 如果需要存储创建的菜单对象，便于重建或销毁，可在此初始化为 None
        self.notes_menu = None

    def load_content(self, content):
        """
        根据保存的文本内容加载便笺，
        当内容中存在图片标记（格式 [[IMG:<图片路径>]]）时，自动读取并插入图片。
        """
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
                    # 调用时将 add_newline 设为 False，避免重复换行
                    self.image_handler.insert_pil_image(image, part, add_newline=False)
                except Exception as e:
                    self.text_widget.insert(tk.END, f"[图片加载失败:{part}]")

    def hide_window(self):
        """窗口关闭时自动保存内容（仅当内容不为空时），然后关闭窗口"""
        self.note_manager.save_note()
        self.root.destroy()

    def minimize_window(self):
        """手动最小化窗口方法（保留可用）"""
        self.root.withdraw()

    def request_new_sticky_note(self):
        global global_command_queue
        if global_command_queue is not None:
            global_command_queue.put("new")

    def show_saved_notes_menu(self, event=None):
        """
        点击 📂 按钮后，在当前便笺窗口中弹出一个下拉菜单，
        其中列出所有已保存的便笺。对每个便笺提供“打开”、“重命名”和“删除”功能。
        """
        from note_manager import NoteManager, SAVE_FILE
        import tkinter.simpledialog as simpledialog
        from tkinter import messagebox

        data = NoteManager.load_notes_list()

        if hasattr(self, "notes_menu") and self.notes_menu:
            self.notes_menu.destroy()

        self.notes_menu = tk.Menu(
            self.root, tearoff=0,
            bg="#3E3E3E", fg="#FFFFFF",
            activebackground="#FFCC00", activeforeground="black"
        )

        if not data:
            self.notes_menu.add_command(label="暂无便笺", state="disabled")
        else:
            for note_id in sorted(data.keys()):
                note_info = data[note_id]
                display_label = note_info.get("name", note_id)

                sub_menu = tk.Menu(
                    self.notes_menu, tearoff=0,
                    bg="#3E3E3E", fg="#FFFFFF",
                    activebackground="#FFCC00", activeforeground="black"
                )

                def open_note(nid=note_id):
                    p = multiprocessing.Process(
                        target=launch_sticky_note,
                        args=(nid, global_command_queue)
                    )
                    p.start()

                def rename_note(nid=note_id):
                    current_name = data[nid].get("name", nid)
                    new_name = simpledialog.askstring(
                        "重命名", "请输入新的便笺名称：",
                        parent=self.root, initialvalue=current_name
                    )
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

    # ========== 新增方法：切换加粗 / 切换斜体 ==========

    def toggle_bold(self):
        """对当前选中的文本加/取消加粗"""
        try:
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
        except tk.TclError:
            return  # 没选中任何文本则不处理

        if self._has_tag_in_range("bold", start, end):
            # 如果选区内“全部”包含 bold，就移除
            self.text_widget.tag_remove("bold", start, end)
        else:
            # 否则添加 bold
            self.text_widget.tag_add("bold", start, end)

    def toggle_italic(self):
        """对当前选中的文本加/取消斜体"""
        try:
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
        except tk.TclError:
            return  # 没选中任何文本则不处理

        if self._has_tag_in_range("italic", start, end):
            self.text_widget.tag_remove("italic", start, end)
        else:
            self.text_widget.tag_add("italic", start, end)

    def _has_tag_in_range(self, tag_name, start, end):
        """
        简化处理：若选区内“完全”覆盖在 tag_name 范围，就返回 True，否则 False。
        实际可实现更精细的检测。
        """
        # 获取该 tag 在整个文本中的所有 [start, end) 对
        ranges = self.text_widget.tag_ranges(tag_name)
        # ranges 成对出现 (start1, end1, start2, end2, ...)
        # 只要找到一个 (tag_start, tag_end) 能完全覆盖 [start, end] 即可
        for i in range(0, len(ranges), 2):
            tag_start = ranges[i]
            tag_end = ranges[i+1]
            if (self.text_widget.compare(tag_start, "<=", start) and
                self.text_widget.compare(tag_end, ">=", end)):
                return True
        return False


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

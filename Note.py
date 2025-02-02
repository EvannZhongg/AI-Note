import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
from ToolTip import ToolTip
import time
import multiprocessing
import re
import json

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
        self.root.title("Note")

        if x is not None and y is not None:
            geometry_str = f"300x400+{x}+{y}"
        else:
            geometry_str = "300x400+100+100"
        self.root.geometry(geometry_str)

        self.root.configure(bg="#2B2B2B")
        self.root.overrideredirect(False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.note_id = note_id or time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.header_bg = "#FFCC00"
        self.text_bg = "#3E3E3E"
        self.text_fg = "#FFFFFF"
        self.is_pinned = False

        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.pack(fill=tk.X, side=tk.TOP)

        # ============ 工具栏按钮 ============
        self.pin_btn = tk.Button(self.header, text="📌", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12))
        ToolTip(self.pin_btn, "固定窗口")

        self.color_btn = tk.Button(self.header, text="🎨", bg=self.header_bg, fg="black", bd=0,
                                   font=("Arial", 12))
        ToolTip(self.color_btn, "更改颜色")

        self.image_btn = tk.Button(self.header, text="📷", bg=self.header_bg, fg="black", bd=0,
                                   font=("Arial", 12))
        ToolTip(self.image_btn, "插入图片")

        self.list_btn = tk.Button(self.header, text="📂", bg=self.header_bg, fg="black", bd=0,
                                  font=("Arial", 12), command=self.show_saved_notes_menu)
        ToolTip(self.list_btn, "查看/管理已保存便笺")

        self.new_btn = tk.Button(self.header, text="➕", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12), command=self.request_new_sticky_note)
        ToolTip(self.new_btn, "新建便笺")

        self.delete_btn = tk.Button(self.header, text="🗑", bg=self.header_bg, fg="black", bd=0,
                                    font=("Arial", 12))
        ToolTip(self.delete_btn, "删除便笺")

        self.bold_btn = tk.Button(self.header, text="B", bg=self.header_bg, fg="black", bd=0,
                                  font=("Arial", 12, "bold"), command=self.toggle_bold)
        ToolTip(self.bold_btn, "加粗")

        self.italic_btn = tk.Button(self.header, text="I", bg=self.header_bg, fg="black", bd=0,
                                    font=("Arial", 12, "italic"), command=self.toggle_italic)
        ToolTip(self.italic_btn, "斜体")

        for btn in [
            self.pin_btn, self.color_btn, self.image_btn,
            self.bold_btn, self.italic_btn,
            self.list_btn, self.new_btn, self.delete_btn
        ]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)

        self.text_widget = tk.Text(
            self.root, wrap="word",
            font=("微软雅黑", 11),
            fg=self.text_fg, bg=self.text_bg,
            borderwidth=0, insertbackground="white",
            relief="flat", padx=10, pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.tag_configure("invisible", elide=True)

        # 配置标签
        self.text_widget.tag_configure("bold", font=("微软雅黑", 11, "bold"), foreground=self.text_fg)
        self.text_widget.tag_configure("italic", font=("微软雅黑", 11, "italic"), foreground=self.text_fg)
        self.text_widget.tag_configure("bold_italic", font=("微软雅黑", 11, "bold", "italic"), foreground=self.text_fg)

        self.shortcut_manager = TextShortcuts(self.text_widget, image_handler=self.image_handler)
        self.note_manager.load_note()
        self.notes_menu = None

    # 点击“➕”时，新便笺在当前窗口右侧
    def request_new_sticky_note(self):
        global global_command_queue
        if global_command_queue is not None:
            geo_str = self.root.geometry()
            import re
            match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geo_str)
            if match:
                width  = int(match.group(1))
                old_x  = int(match.group(3))
                old_y  = int(match.group(4))
            else:
                old_x, old_y = 100, 100
                width = 300
            new_x = old_x + width + 30
            new_y = old_y
            global_command_queue.put(("new_with_xy", new_x, new_y))

    def hide_window(self):
        self.note_manager.save_note()
        self.root.destroy()

    def minimize_window(self):
        self.root.withdraw()

    def show_saved_notes_menu(self, event=None):
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
                    self.root, tearoff=0,
                    bg="#3E3E3E", fg="#FFFFFF",
                    activebackground="#FFCC00", activeforeground="black"
                )

                def open_note(nid=note_id):
                    # =========== 改动：打开已保存便笺，也使用 open_with_xy ===========
                    geo_str2 = self.root.geometry()
                    match2 = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geo_str2)
                    if match2:
                        w2 = int(match2.group(1))
                        ox2 = int(match2.group(3))
                        oy2 = int(match2.group(4))
                    else:
                        ox2, oy2 = 100, 100
                        w2 = 300
                    nx2 = ox2 + w2 + 30
                    ny2 = oy2
                    # 发送 ("open_with_xy", note_id, nx2, ny2)
                    global global_command_queue
                    if global_command_queue:
                        global_command_queue.put(("open_with_xy", nid, nx2, ny2))

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
            tag_end = ranges[i+1]
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

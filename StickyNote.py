import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls
import multiprocessing  # 用于多进程

class StickyNote:
    def __init__(self, note_id=None, master=None):
        """
        如果传入 master 则在该 master 上创建 Toplevel 窗口，
        否则创建一个独立的 Tk() 窗口（适用于独立进程）。
        """
        if master is None:
            self.root = tk.Tk()  # 独立进程中，创建自己的主窗口
        else:
            self.root = tk.Toplevel(master)
        self.root.title("便笺")
        self.root.geometry("300x400+100+100")
        self.root.configure(bg="#2B2B2B")
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # **便笺标识**
        self.note_id = note_id or str(len(NoteManager.load_notes_list()) + 1)  # 确保是字符串
        self.header_bg = "#FFCC00"
        self.text_bg = "#3E3E3E"
        self.text_fg = "#FFFFFF"
        self.is_pinned = False

        # **创建标题栏**
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.pack(fill=tk.X, side=tk.TOP)

        # **创建按钮**
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
        self.list_btn = tk.Button(self.header, text="📂", bg=self.header_bg, fg="black", bd=0,
                                  font=("Arial", 12))
        # 新便笺按钮调用全局的 create_new_sticky_note（会生成独立进程）
        self.new_btn = tk.Button(self.header, text="➕", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12), command=create_new_sticky_note)
        self.delete_btn = tk.Button(self.header, text="🗑", bg=self.header_bg, fg="black", bd=0,
                                    font=("Arial", 12))

        # **添加按钮到界面**
        for btn in [self.close_btn, self.min_btn, self.pin_btn, self.color_btn,
                    self.image_btn, self.list_btn, self.new_btn, self.delete_btn]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # **初始化 NoteManager**
        self.note_manager = NoteManager(self)

        # **初始化 ImageHandler**
        self.image_handler = ImageHandler(self)

        # **初始化 WindowControls**
        self.window_controls = WindowControls(self)

        # **创建文本输入框**
        self.text_widget = tk.Text(self.root, wrap="word", font=("Arial", 14),
                                   fg=self.text_fg, bg=self.text_bg,
                                   borderwidth=0, insertbackground="white",
                                   relief="flat", padx=10, pady=10)
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # **绑定快捷键和粘贴功能**
        self.shortcut_manager = TextShortcuts(self.text_widget)
        self.root.bind("<Control-v>", self.image_handler.paste)

        # **加载便笺内容**
        self.note_manager.load_note()

    def hide_window(self):
        """只关闭当前窗口，不影响其他窗口"""
        self.note_manager.save_note()
        self.root.destroy()

    def minimize_window(self):
        """最小化当前窗口"""
        self.root.withdraw()

def launch_sticky_note(note_id=None):
    """
    用于多进程调用的函数：
    创建一个 StickyNote 实例并启动自己的 mainloop。
    """
    note = StickyNote(note_id=note_id, master=None)
    note.root.mainloop()

def create_new_sticky_note():
    """使用多进程独立创建新便笺窗口"""
    p = multiprocessing.Process(target=launch_sticky_note)
    p.start()

if __name__ == "__main__":
    # 单独运行此文件时，直接创建一个便笺窗口
    launch_sticky_note()

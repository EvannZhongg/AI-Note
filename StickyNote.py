import tkinter as tk
from text_shortcuts import TextShortcuts
from note_manager import NoteManager
from image_handler import ImageHandler
from window_controls import WindowControls

# 全局变量，用于保存主进程传入的命令队列（用于新建便笺）
global_command_queue = None

class StickyNote:
    def __init__(self, note_id=None):
        # 每个进程中，独立创建自己的主窗口
        self.root = tk.Tk()
        self.root.title("便笺")
        self.root.geometry("300x400+100+100")
        self.root.configure(bg="#2B2B2B")
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # 便笺标识（此处为了简化直接使用 "1"）
        self.note_id = note_id or "1"
        self.header_bg = "#FFCC00"
        self.text_bg = "#3E3E3E"
        self.text_fg = "#FFFFFF"
        self.is_pinned = False

        # 创建标题栏
        self.header = tk.Frame(self.root, bg=self.header_bg, height=30, relief="flat", bd=0)
        self.header.pack(fill=tk.X, side=tk.TOP)

        # 创建按钮
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
        # “➕”按钮：点击时通过命令队列通知主进程新建便笺窗口
        self.new_btn = tk.Button(self.header, text="➕", bg=self.header_bg, fg="black", bd=0,
                                 font=("Arial", 12), command=self.request_new_sticky_note)
        self.delete_btn = tk.Button(self.header, text="🗑", bg=self.header_bg, fg="black", bd=0,
                                    font=("Arial", 12))

        # 将所有按钮添加到标题栏
        for btn in [self.close_btn, self.min_btn, self.pin_btn, self.color_btn,
                    self.image_btn, self.list_btn, self.new_btn, self.delete_btn]:
            btn.pack(side=tk.RIGHT, padx=5, pady=3)

        # 初始化各模块
        self.note_manager = NoteManager(self)
        self.image_handler = ImageHandler(self)
        self.window_controls = WindowControls(self)

        # 创建文本编辑区
        self.text_widget = tk.Text(self.root, wrap="word", font=("Arial", 14),
                                   fg=self.text_fg, bg=self.text_bg,
                                   borderwidth=0, insertbackground="white",
                                   relief="flat", padx=10, pady=10)
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        self.shortcut_manager = TextShortcuts(self.text_widget)
        self.root.bind("<Control-v>", self.image_handler.paste)

        # 可在此加载便笺内容（示例中略过）

    def hide_window(self):
        """关闭当前便笺窗口（同时保存内容）"""
        self.note_manager.save_note()
        self.root.destroy()

    def minimize_window(self):
        """最小化窗口"""
        self.root.withdraw()

    def request_new_sticky_note(self):
        """点击➕时，通过全局命令队列向主进程发送新建请求"""
        global global_command_queue
        if global_command_queue is not None:
            global_command_queue.put("new")

def launch_sticky_note(note_id=None, command_queue=None):
    """
    用于多进程调用：设置全局命令队列，并创建便笺窗口后进入事件循环。
    参数：
      - note_id: 便笺标识（可选）
      - command_queue: 主进程传入的队列，用于接收新建便笺的请求
    """
    global global_command_queue
    global_command_queue = command_queue
    note = StickyNote(note_id=note_id)
    note.root.mainloop()

if __name__ == "__main__":
    # 方便单独测试时运行
    launch_sticky_note()

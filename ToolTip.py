import tkinter as tk

class ToolTip:
    """
    基础的工具提示类。将此类放在单独的 ToolTip.py 文件中。
    使用示例:
        from ToolTip import ToolTip
        ...
        some_button = tk.Button(...)
        ToolTip(some_button, "这是按钮的提示文字")
    """
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tip_window = None

        # 绑定鼠标进入/离开事件
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """当鼠标进入控件时，创建一个无边框的小窗口显示提示文本"""
        if self.tip_window or not self.text:
            return

        # 计算弹出位置：让 tooltip 出现在控件右侧或下方
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height()

        # 创建一个 Toplevel，无边框
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.attributes("-topmost", True)
        tw.wm_overrideredirect(True)  # 去掉标题栏和边框
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#FFFFE0", relief="solid", borderwidth=1,
            font=("tahoma", 8, "normal")
        )
        label.pack(ipadx=1, ipady=1)

    def hide_tooltip(self, event=None):
        """鼠标离开控件时，销毁提示窗口"""
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

import tkinter as tk

class TextShortcuts:
    def __init__(self, text_widget):
        """初始化快捷键绑定"""
        self.text_widget = text_widget
        self.bind_shortcuts()

    def bind_shortcuts(self):
        """绑定文本编辑的快捷键"""
        self.text_widget.bind("<Control-z>", self.undo)
        self.text_widget.bind("<Control-y>", self.redo)
        self.text_widget.bind("<Control-x>", self.cut)
        self.text_widget.bind("<Control-c>", self.copy)
        self.text_widget.bind("<Control-v>", self.paste)
        self.text_widget.bind("<Control-a>", self.select_all)
        self.text_widget.bind("<Delete>", self.delete_selected)

    def undo(self, event=None):
        """撤销 (Ctrl + Z)"""
        try:
            self.text_widget.edit_undo()
        except tk.TclError:
            pass  # 没有可撤销的操作

    def redo(self, event=None):
        """重做 (Ctrl + Y)"""
        try:
            self.text_widget.edit_redo()
        except tk.TclError:
            pass  # 没有可重做的操作

    def cut(self, event=None):
        """剪切 (Ctrl + X)"""
        self.copy()
        self.delete_selected()

    def copy(self, event=None):
        """复制 (Ctrl + C)"""
        try:
            selected_text = self.text_widget.selection_get()
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(selected_text)
        except tk.TclError:
            pass  # 没有选中内容

    def paste(self, event=None):
        """粘贴 (Ctrl + V)"""
        try:
            clipboard_content = self.text_widget.clipboard_get()
            self.text_widget.insert(tk.INSERT, clipboard_content)
        except tk.TclError:
            pass  # 剪贴板为空

    def select_all(self, event=None):
        """全选 (Ctrl + A)"""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        return "break"  # 阻止默认行为

    def delete_selected(self, event=None):
        """删除选中的文本"""
        try:
            self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # 没有选中内容

# **确保 `text_shortcuts.py` 只作为模块被导入，而不能直接运行**
if __name__ == "__main__":
    print("此文件是一个模块，不应直接运行")

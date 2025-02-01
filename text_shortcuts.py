import tkinter as tk


class TextShortcuts:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.bind_shortcuts()

    def bind_shortcuts(self):
        self.text_widget.bind("<Control-z>", self.undo)
        self.text_widget.bind("<Control-y>", self.redo)
        self.text_widget.bind("<Control-x>", self.cut)
        self.text_widget.bind("<Control-c>", self.copy)
        self.text_widget.bind("<Control-v>", self.paste)
        self.text_widget.bind("<Control-a>", self.select_all)

        # 同时拦截 Delete 和 BackSpace，由同一函数 handle_delete_or_backspace 处理
        self.text_widget.bind("<Delete>", self.handle_delete_or_backspace)
        self.text_widget.bind("<BackSpace>", self.handle_delete_or_backspace)

    def undo(self, event=None):
        try:
            self.text_widget.edit_undo()
        except tk.TclError:
            pass

    def redo(self, event=None):
        try:
            self.text_widget.edit_redo()
        except tk.TclError:
            pass

    def cut(self, event=None):
        self.copy()
        self.delete_selected()

    def copy(self, event=None):
        try:
            selected_text = self.text_widget.selection_get()
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def paste(self, event=None):
        try:
            clipboard_content = self.text_widget.clipboard_get()
            self.text_widget.insert(tk.INSERT, clipboard_content)
        except tk.TclError:
            pass

    def select_all(self, event=None):
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        return "break"

    def delete_selected(self):
        """如果有选中区域，则删除选中区域，否则什么也不做。"""
        widget = self.text_widget
        try:
            start = widget.index(tk.SEL_FIRST)
            end = widget.index(tk.SEL_LAST)
            widget.delete(start, end)
        except tk.TclError:
            pass

    def handle_delete_or_backspace(self, event=None):
        """
        统一处理 Delete/BackSpace 两种键。
        - Delete：删除光标右侧字符
        - BackSpace：删除光标左侧字符
        然后根据实际删除位置，检查是否紧邻或包含 "invisible" 标签区域，如果是则一并删除。
        """
        widget = self.text_widget

        # 先看是否有选区，如果有，则删掉选区后直接返回
        try:
            start = widget.index(tk.SEL_FIRST)
            end = widget.index(tk.SEL_LAST)
            widget.delete(start, end)
            # 删除选区后，再看看是否能删除隐藏标记
            self._check_invisible_after_delete(start, start, event.keysym)
            return "break"
        except tk.TclError:
            pass

        # 没有选区，根据是 Delete 还是 BackSpace 决定删除方向
        if event.keysym == "Delete":
            # Delete：删除光标右侧字符
            delete_index = widget.index("insert")
            next_index = widget.index("insert +1c")
            widget.delete(delete_index, next_index)
            self._check_invisible_after_delete(delete_index, delete_index, "Delete")
        elif event.keysym == "BackSpace":
            # BackSpace：删除光标左侧字符
            delete_index = widget.index("insert -1c")
            widget.delete(delete_index, widget.index("insert"))
            self._check_invisible_after_delete(delete_index, delete_index, "BackSpace")

        return "break"

    def _check_invisible_after_delete(self, start_index, delete_index, key):
        """
        删除后检查附近是否有 "invisible" 标签，如果有则将其整个删除。

        参数:
          - start_index: 选区删除或光标删除的开始位置
          - delete_index: 删除后光标所在位置
          - key: "Delete" 或 "BackSpace"，用于辅助判断方向
        """
        widget = self.text_widget

        # 先把当前插入点取出来，后面备用
        current_insert = widget.index("insert")

        # 如果是 Delete，可能隐藏标记在 delete_index 开头
        if key == "Delete":
            # 查找下一段 "invisible"
            inv_range = widget.tag_nextrange("invisible", delete_index)
            if inv_range and widget.compare(inv_range[0], "==", delete_index):
                widget.delete(inv_range[0], inv_range[1])
                return

            # 如果没找到，就再看看是否在 current_insert 位置有 invisible
            inv_range = widget.tag_prevrange("invisible", current_insert)
            if inv_range and widget.compare(inv_range[1], "==", current_insert):
                widget.delete(inv_range[0], inv_range[1])
                return

        elif key == "BackSpace":
            # 如果是 BackSpace，可能隐藏标记在 delete_index 前面
            # 先看看 delete_index 是否在某段 invisible 的末尾
            inv_range = widget.tag_prevrange("invisible", delete_index)
            if inv_range and widget.compare(inv_range[1], "==", delete_index):
                widget.delete(inv_range[0], inv_range[1])
                return

            # 如果没找到，就再看看是否在 current_insert 位置有 invisible
            inv_range = widget.tag_nextrange("invisible", current_insert)
            if inv_range and widget.compare(inv_range[0], "==", current_insert):
                widget.delete(inv_range[0], inv_range[1])
                return

        # 如果上面都没找到，就说明此时没有紧邻的 invisible 文本段
        return

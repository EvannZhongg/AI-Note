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
        self.text_widget.bind("<Delete>", self.delete_selected)

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

    def delete_selected(self, event=None):
        try:
            self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

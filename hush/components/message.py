from tkinter import messagebox, Tk, Toplevel, filedialog
from typing import Literal, Optional, Union


def mbox(title: str, text: str, style: Literal[0, 1, 2, 3], parent: Optional[Union[Tk, Toplevel]] = None):
    """Message Box, made simpler
    ##  Styles:
    ##  0 : info
    ##  1 : warning
    ##  2 : error
    ##  3 : Yes No
    """
    if style == 0:
        return messagebox.showinfo(title, text, parent=parent)  # Return ok x same as ok
    elif style == 1:
        return messagebox.showwarning(title, text, parent=parent)  # Return ok x same as ok
    elif style == 2:
        return messagebox.showerror(title, text, parent=parent)  # Return ok x same as ok
    elif style == 3:
        return messagebox.askyesno(title, text, parent=parent)  # Return True False, x can't be clicked


def ask_file_sound(title: str, parent: Optional[Union[Tk, Toplevel]] = None):
    return filedialog.askopenfilename(
        title=title,
        parent=parent,
        filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac *.m4a *.wma *.aac"), ("All Files", "*.*")]
    )

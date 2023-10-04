from os import startfile
from subprocess import Popen
import tkinter as tk
from random import choice
from tkinter import ttk
from typing import Dict, Union
from webbrowser import open_new
from difflib import SequenceMatcher

from notifypy import Notify, exceptions
from PIL import Image, ImageDraw, ImageFont, ImageTk

from hush._path import app_icon, app_icon_missing
from hush.custom_logging import logger

APP_NAME = "Hush"


def up_first_case(string: str):
    return string[0].upper() + string[1:]


def get_similar_keys(_dict: Dict, key: str):
    return [k for k in _dict.keys() if key.lower() in k.lower()]


def get_proxies(proxy_http: str, proxy_https: str):
    """
    Proxies in setting is saved in a string format separated by \n
    This function will convert it to a dict format and get the proxies randomly
    """
    proxies = {}
    if proxy_http != "":
        http_list = proxy_http.split()
        http_list = [word for word in http_list if any(char.isalpha() for char in word)]
        proxies["http"] = choice(http_list)
    if proxy_https != "":
        https_list = proxy_https.split()
        https_list = [word for word in https_list if any(char.isalpha() for char in word)]
        proxies["https"] = choice(https_list)
    return proxies


def cbtn_invoker(settingVal: bool, widget: Union[ttk.Checkbutton, ttk.Radiobutton]):
    """
    Checkbutton invoker
    Invoking twice will make it unchecked
    """
    if settingVal:
        widget.invoke()
    else:
        widget.invoke()
        widget.invoke()


def OpenUrl(url: str):
    """
    To open a url in the default browser
    """
    try:
        open_new(url)
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error", "Cannot open the url specified.")


def start_file(filename: str):
    """
    Open a folder or file in the default application.
    """
    try:
        startfile(filename)
    except FileNotFoundError:
        logger.exception("Cannot find the file specified.")
        nativeNotify("Error", "Cannot find the file specified.")
    except Exception:
        try:
            Popen(["xdg-open", filename])
        except FileNotFoundError:
            logger.exception("Cannot open the file specified.")
            nativeNotify("Error", "Cannot find the file specified.")
        except Exception as e:
            logger.exception("Error: " + str(e))
            nativeNotify("Error", f"Uncaught error {str(e)}")


def get_channel_int(channel_string: str):
    if channel_string.isdigit():
        return int(channel_string)
    elif channel_string.lower() == "mono":
        return 1
    elif channel_string.lower() == "stereo":
        return 2
    else:
        raise ValueError("Invalid channel string")


def nativeNotify(title: str, message: str):
    """
    Native notification
    """
    notification = Notify()
    notification.application_name = APP_NAME
    notification.title = title
    notification.message = message
    if not app_icon_missing:
        try:
            notification.icon = app_icon
        except exceptions:
            pass

    notification.send()


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def popup_menu(root: Union[tk.Tk, tk.Toplevel], menu: tk.Menu, open: bool = True):
    """
    Display popup menu
    """
    try:
        if open:
            menu.tk_popup(root.winfo_pointerx(), root.winfo_pointery(), 0)
    finally:
        menu.grab_release()


def emoji_img(size, text):
    font = ImageFont.truetype("seguiemj.ttf", size=int(round(size * 72 / 96, 0)))
    # pixels = points * 96 / 72 : 96 is windowsDPI
    im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(im)
    draw.text((size / 2, size / 2), text, embedded_color=True, font=font, anchor="mm")
    return ImageTk.PhotoImage(im)


def bind_focus_recursively(root, root_widget):
    """
    Bind focus on widgets recursively
    """
    widgets = root_widget.winfo_children()

    # now check if there are any children of the children
    for widget in widgets:
        if len(widget.winfo_children()) > 0:
            bind_focus_recursively(root, widget)

        if (
            isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame) or isinstance(widget, tk.LabelFrame)
            or isinstance(widget, ttk.LabelFrame) or isinstance(widget, tk.Label) or isinstance(widget, ttk.Label)
        ):
            # make sure that Button-1 is not already binded
            if "<Button-1>" not in widget.bind():
                widget.bind("<Button-1>", lambda event: root.focus_set())

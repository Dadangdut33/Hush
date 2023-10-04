import os
from threading import Thread
from tkinter import Tk, ttk, Menu, BooleanVar
from signal import SIGINT, signal
from typing import Dict, Literal  # Import the signal module to handle Ctrl+C

import pyaudio
from PIL import Image, ImageDraw
from pystray import Icon as icon, Menu as menu, MenuItem as item
from pygame import mixer
from requests import get
from webrtcvad import Vad

from .components.tooltip import tk_tooltip, tk_tooltips
from .components.audio import AudioMeter
from .components.message import mbox, ask_file_sound

from .utils.audio.device import (
    get_default_host_api, get_default_input_device, get_device_details, get_db, get_host_apis, get_input_devices
)
from .utils.helper import (
    OpenUrl, bind_focus_recursively, emoji_img, get_channel_int, nativeNotify, popup_menu, similar, start_file
)

from ._path import app_icon, app_icon_missing, beep_default, dir_log
from ._version import __version__
from .globals import gc, sj
from .custom_logging import logger

APP_NAME = "Hush"
MAX_THRESHOLD = 1
MIN_THRESHOLD = -81


# Function to handle Ctrl+C and exit just like clicking the exit button
def signal_handler(sig, frame):
    logger.info("Received Ctrl+C, exiting...")

    gc.running = False


signal(SIGINT, signal_handler)  # Register the signal handler for Ctrl+C


class AppTray:
    """
    Tray app
    """
    def __init__(self):
        self.icon: icon = None  # type: ignore
        self.menu: menu = None  # type: ignore
        self.menu_items = None  # type: ignore
        gc.tray = self
        self.create_tray()
        logger.info("Tray created")

    # -- Tray icon
    def create_image(self, width, height, color1, color2):
        # Generate an image and draw a pattern
        image = Image.new("RGB", (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)

        return image

    # -- Create tray
    def create_tray(self):
        try:
            trayIco = Image.open(app_icon)
        except Exception:
            trayIco = self.create_image(64, 64, "black", "white")

        self.menu_items = (
            item(f"{APP_NAME} {__version__}", lambda *args: None, enabled=False),  # do nothing
            menu.SEPARATOR,
            item("Show", self.open_app),
            item("Exit", self.exit_app),
            item("Hidden onclick", self.open_app, default=True, visible=False),  # onclick the icon will open_app
        )
        self.menu = menu(*self.menu_items)
        self.icon = icon(APP_NAME, trayIco, f"Speech Translate V{__version__}", self.menu)
        self.icon.run_detached()

    # -- Open app
    def open_app(self):
        assert gc.mw is not None  # Show main window
        gc.mw.show_window()

    # -- Exit app by flagging runing false to stop main loop
    def exit_app(self):
        gc.running = False


class Hush:
    def __init__(self):
        gc.mw = self
        self.checking = False
        self.notified = False
        self.max_v = 0
        self.min_v = 0
        self.vad = Vad() if sj.cache["vad_mode"] == "Off" else Vad(int(sj.cache["vad_mode"]))
        self.is_speech = False
        self.detail_device = None
        self.p_rec = None
        self.stream_rec = None
        self.streaming = False

        self.root = Tk()
        self.wrench_emoji = emoji_img(16, "     🛠️")

        self.root.title(APP_NAME)
        self.root.geometry(sj.cache["mw_size"])
        self.root.minsize(500, 225)
        self.root.maxsize(1000, 250)
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        if not app_icon_missing:
            self.root.iconbitmap(app_icon)

        # menu
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.file_menu = Menu(self.menu, tearoff=False)
        self.file_menu.add_command(label="Hide", command=self.close_window)
        self.file_menu.add_command(label="Exit", command=self.quit_app)
        self.menu.add_cascade(label="File", menu=self.file_menu)

        self.option_menu = Menu(self.menu, tearoff=False)
        self.beep_submenu = Menu(self.option_menu, tearoff=False)
        self.beep_submenu.add_command(label="Change beep sound", command=lambda: self.change_beep())
        self.beep_submenu.add_command(label="Set to default", command=lambda: self.beep_set_default())

        self.log_submenu = Menu(self.option_menu, tearoff=False)
        self.keep_log = BooleanVar(self.root, sj.cache["keep_log"])
        self.log_submenu.add_command(label="Open log folder", command=lambda: start_file(dir_log))
        self.log_submenu.add_checkbutton(
            label="Keep log", variable=self.keep_log, command=lambda: sj.save_key("keep_log", self.keep_log.get())
        )
        self.log_submenu.add_command(label="Clear log", command=lambda: self.clear_log())

        self.option_menu.add_cascade(label="Beep option", menu=self.beep_submenu)
        self.option_menu.add_cascade(label="Log", menu=self.log_submenu)
        self.option_menu.add_command(label="Reset all setting to default", command=lambda: self.reset_all_setting())

        self.menu.add_cascade(label="Option", menu=self.option_menu)

        self.help_menu = Menu(self.menu, tearoff=False)
        self.help_menu.add_command(label="About", command=self.about)
        self.help_menu.add_command(label="Check for updates", command=lambda: self.check_for_update())
        self.help_menu.add_command(label="Visit App Repository", command=lambda: OpenUrl("https://github.com/Dadangdut33/Hush/"))
        self.menu.add_cascade(label="Help", menu=self.help_menu)

        # frame is divided into 3 main part
        self.mf_1 = ttk.Frame(self.root)
        self.mf_1.pack(side="top", fill="x", expand=True, pady=5)

        self.mf_2 = ttk.Frame(self.root)
        self.mf_2.pack(side="top", fill="both", expand=True, pady=0)

        self.mf_3 = ttk.Frame(self.root)
        self.mf_3.pack(side="bottom", fill="x", expand=True, pady=(0, 5))

        self.mf_1_1 = ttk.Frame(self.mf_1)
        self.mf_1_1.pack(side="top", fill="x", expand=True)

        self.mf_1_2 = ttk.Frame(self.mf_1)
        self.mf_1_2.pack(side="top", fill="x", expand=True)

        self.mf_1_3 = ttk.Frame(self.mf_1)
        self.mf_1_3.pack(side="top", fill="x", expand=True)

        self.mf_2_1 = ttk.Frame(self.mf_2)
        self.mf_2_1.pack(side="top", fill="x", expand=True)

        self.mf_2_2 = ttk.Frame(self.mf_2)
        self.mf_2_2.pack(side="top", fill="x", expand=True)

        self.mf_2_3 = ttk.Frame(self.mf_2)
        self.mf_2_3.pack(side="top", fill="x", expand=True)

        self.mf_2_4 = ttk.Frame(self.mf_2)
        self.mf_2_4.pack(side="top", fill="x", expand=True)

        self.mf_3_1 = ttk.Frame(self.mf_3)
        self.mf_3_1.pack(side="top", fill="x", expand=True)

        self.mf_3_1_l = ttk.Frame(self.mf_3_1)
        self.mf_3_1_l.pack(side="left", fill="x", expand=True)

        self.mf_3_1_r = ttk.Frame(self.mf_3_1)
        self.mf_3_1_r.pack(side="right", fill="x", expand=True)

        # -- mf_1_1
        self.lbl_hostAPI = ttk.Label(self.mf_1_1, text="HostAPI", font="TkDefaultFont 9 bold", width=10)
        self.lbl_hostAPI.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hostAPI,
            "HostAPI for the input device. There are many hostAPI for your device and it is recommended to follow the "
            "default value, other than that it might not work or crash the app.",
            wrapLength=350,
        )

        self.cb_hostAPI = ttk.Combobox(self.mf_1_1, values=[], state="readonly")
        self.cb_hostAPI.bind(
            "<<ComboboxSelected>>", lambda _: sj.save_key("hostAPI", self.cb_hostAPI.get()) or self.hostAPI_change()
        )
        self.cb_hostAPI.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_config_hostAPI = ttk.Button(
            self.mf_1_1,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_hostAPI, not self.streaming),
        )
        self.btn_config_hostAPI.pack(side="left", padx=(5, 10))
        self.menu_hostAPI = self.input_device_menu("hostAPI")

        self.lbl_sample_rate = ttk.Label(self.mf_1_1, text="Sample rate", font="TkDefaultFont 9 bold", width=10)
        self.lbl_sample_rate.pack(side="left", padx=5)

        self.cb_sample_rate = ttk.Combobox(self.mf_1_1, values=["8000", "16000", "32000", "48000"], state="readonly")
        self.cb_sample_rate.set(sj.cache["sample_rate"])
        self.cb_sample_rate.bind(
            "<<ComboboxSelected>>", lambda _: sj.save_key("sample_rate", self.cb_sample_rate.get()) or self.hostAPI_change()
        )
        self.cb_sample_rate.pack(side="left", padx=5, expand=True, fill="x")

        # -- mf_1_2
        self.lbl_device = ttk.Label(self.mf_1_2, text="Device", font="TkDefaultFont 9 bold", width=10)
        self.lbl_device.pack(side="left", padx=5)

        self.cb_device = ttk.Combobox(self.mf_1_2, values=[], state="readonly")
        self.cb_device.bind("<<ComboboxSelected>>", lambda _: sj.save_key("device", self.cb_device.get()))
        self.cb_device.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_config_device = ttk.Button(
            self.mf_1_2,
            image=self.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_device, not self.streaming),
        )
        self.btn_config_device.pack(side="left", padx=(5, 10))
        self.menu_device = self.input_device_menu("device")

        self.lbl_channel = ttk.Label(self.mf_1_2, text="Channel", font="TkDefaultFont 9 bold", width=10)
        self.lbl_channel.pack(side="left", padx=5)

        self.cb_channel = ttk.Combobox(self.mf_1_2, values=["Mono", "Stereo"], state="readonly")
        self.cb_channel.set(sj.cache["channel"])
        self.cb_channel.bind("<<ComboboxSelected>>", lambda _: sj.save_key("channel", self.cb_channel.get()))
        self.cb_channel.pack(side="left", padx=5, expand=True, fill="x")

        # -- mf_1_3
        self.divider_1 = ttk.Separator(self.mf_1_3, orient="horizontal")
        self.divider_1.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # -- mf_2_1
        self.lbl_vad_mode = ttk.Label(self.mf_2_1, text="Filter Noise", font="TkDefaultFont 9 bold", width=10)
        self.lbl_vad_mode.pack(side="left", padx=5)

        self.cb_vad_mode = ttk.Combobox(self.mf_2_1, values=["Off", "1", "2", "3"], state="readonly")
        self.cb_vad_mode.set("3")
        self.cb_vad_mode.bind("<<ComboboxSelected>>", self.vad_mode_change)
        self.cb_vad_mode.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_vad_mode, self.cb_vad_mode],
            "Set the sensitivity level for the voice activity detection (VAD). 0 is the least aggressive in filtering out"
            " non-speech, 3 is the most aggressive",
            wrapLength=350,
        )

        self.vol_low_emoji = emoji_img(16, "     🔉")
        self.vol_high_emoji = emoji_img(16, "     🔊")
        self.lbl_volume_low = ttk.Label(self.mf_2_1, text="100", font="TkDefaultFont 9 bold", image=self.vol_low_emoji)
        self.lbl_volume_low.pack(side="left", padx=5)

        self.slider_volume = ttk.Scale(
            self.mf_2_1,
            from_=0,
            to=100,
            orient="horizontal",
            value=sj.cache["beep_volume"],
            command=lambda e: self.lbl_volume_high.configure(text=round(float(e))),
        )
        self.slider_volume.bind("<ButtonRelease-1>", lambda e: sj.save_key("beep_volume", float(self.slider_volume.get())))
        self.slider_volume.pack(side="left", padx=5, expand=True, fill="x")

        self.lbl_volume_high = ttk.Label(
            self.mf_2_1, text=round(sj.cache["beep_volume"]), image=self.vol_high_emoji, compound="left"
        )
        self.lbl_volume_high.pack(side="left", padx=5)

        # -- mf_2_2
        self.lbl_beep_when = ttk.Label(self.mf_2_2, text="Beep when db is", font="TkDefaultFont 9 bold", width=14)
        self.lbl_beep_when.pack(side="left", padx=5)

        self.slider_beep_when = ttk.Scale(
            self.mf_2_2,
            from_=-80,
            to=0,
            orient="horizontal",
            command=self.slider_beeper_move,
        )
        self.slider_beep_when.bind(
            "<ButtonRelease-1>", lambda e: sj.save_key("beep_when_reach", float(self.slider_beep_when.get()))
        )
        self.slider_beep_when.pack(side="left", padx=5, expand=True, fill="x")

        self.lbl_beep_when_value = ttk.Label(self.mf_2_2, text="-5 db")
        self.lbl_beep_when_value.pack(side="left", padx=5)

        # -- mf_2_3
        self.audio_meter = AudioMeter(
            self.mf_2_3,
            self.root,
            width=300,
            height=40,
            min=-80,
            max=0,
            threshold=sj.cache["beep_when_reach"],
            show_threshold=True,
            auto_resize=True
        )
        self.audio_meter.pack(side="top", padx=5, pady=(5, 0), expand=True, fill="both")

        # -- mf_2_4
        self.divider_2 = ttk.Separator(self.mf_2_3, orient="horizontal")
        self.divider_2.pack(side="left", fill="x", expand=True, padx=5, pady=(5, 0))

        # -- mf_3_1_l
        self.lbl_version = ttk.Label(self.mf_3_1_l, text=f"Version: {__version__}")
        self.lbl_version.pack(side="left", padx=5)
        self.tooltip_version = tk_tooltip(self.lbl_version, __version__)

        self.lbl_vad_status = ttk.Label(self.mf_3_1_l, text="VAD: Off" if sj.cache["vad_mode"] == "Off" else "VAD: On")
        self.lbl_vad_status.pack(side="left", padx=5)

        # -- mf_3_1_r
        self.btn_toggle_start_hush = ttk.Button(self.mf_3_1_r, text="Start", command=self.start_hush)
        self.btn_toggle_start_hush.pack(side="right", padx=5)

        # --------------------------
        bind_focus_recursively(self.root, self.root)
        self.cb_input_device_init()
        self.init_mixer_with_check()
        self.slider_beep_when.set(sj.cache["beep_when_reach"])  # after everything is set
        gc.running_after_id = self.root.after(1000, self.is_running_poll)
        if sj.cache["checkUpdateOnStart"]:
            self.check_for_update(onStart=True)
        if not sj.cache["keep_log"]:
            self.clear_log(on_start=True)

    # ----------------------------------------------------------------------
    def show_window(self):
        self.root.after(0, self.root.deiconify)

    def close_window(self):
        if not self.notified:
            nativeNotify("Hush is still running", "Hush is still running in the background")
            self.notified = True

        self.root.withdraw()

    def save_win_size(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sj.save_key("mw_size", f"{w}x{h}")

    def cleanup(self):
        # cancel the is_running_poll
        self.root.after_cancel(gc.running_after_id)

        # stop the audio
        mixer.quit()
        self.close_hush_meter()

        if gc.tray:
            gc.tray.icon.stop()

        logger.info("Destroying windows...")
        self.root.destroy()

    def is_running_poll(self):
        if not gc.running:
            self.quit_app()

        gc.running_after_id = self.root.after(1000, self.is_running_poll)

    def quit_app(self):
        self.save_win_size()
        self.cleanup()

        try:
            os._exit(0)
        except SystemExit:
            logger.info("Exit successful")

    def clear_log(self, on_start=False):
        if not on_start:
            if mbox(
                "Confirmation",
                "Are you sure you want to clear log directory? This action cannot be undone",
                3,
                self.root,
            ):
                # clear log
                self.clear_the_log()
                mbox("Success", "Log directory has been cleared", 0, self.root)
        else:
            # clear log
            self.clear_the_log()

    def clear_the_log(self):
        try:
            logger.info("Clearing log directory...")
            for f in os.listdir(dir_log):
                os.remove(os.path.join(dir_log, f))
        except Exception as e:
            if "it is being used by another process" not in str(e):
                logger.exception(e)

    # ----------------------------------------------------------------------
    def about(self):
        mbox(
            "About",
            f"{APP_NAME} {__version__}\n\nA simple mic loudness notifier that you can use when you need to be as silent as "
            "possible. It is useful especially when you are gaming and you know... got really got into it"
            ", not noticing that you are very very loud and then your neighbor or your housemate knocks on your door "
            "and tell you to sshhh", 0, self.root
        )

    def change_beep(self):
        """
        Change beep sound
        """
        mbox(
            "Information",
            "Please make sure that the sound is short and it starts immediately so that it can be played correctly"
            "\n\nTry to trim the start of your audio if the program does not play the beep when it should", 0
        )

        f = ask_file_sound("Select the sound file that you want to use as beep sound", self.root)
        if f:
            sj.save_key("custom_beep_path", f)
            self.init_mixer_with_check()
            mixer.music.load(f)
            mbox("Success", "Beep sound has been changed successfully", 0, self.root)

    def beep_set_default(self):
        """
        Set beep sound to default
        """
        # ask confirmation
        if mbox(
            "Confirmation",
            "Are you sure you want to set the beep sound to default? ",
            3,
            self.root,
        ):
            sj.save_key("custom_beep_path", "")
            self.init_mixer_with_check()
            mixer.music.load(beep_default)
            mbox("Success", "Beep sound has been set to default", 0, self.root)

    def reset_all_setting(self):
        if mbox(
            "Confirmation",
            "Are you sure you want to reset all setting to default? ",
            3,
            self.root,
        ):
            sj.createDefaultSetting()
            self.cb_input_device_init()
            self.cb_sample_rate.set(sj.cache["sample_rate"])
            self.cb_channel.set(sj.cache["channel"])
            self.slider_volume.set(sj.cache["beep_volume"])
            self.slider_beep_when.set(sj.cache["beep_when_reach"])
            self.vad_mode_change(sj.cache["vad_mode"])
            self.init_mixer_with_check()
            self.beep_set_default()
            mbox("Success", "All setting has been reset to default", 0, self.root)

    # ---------------------------------------------------------------------
    def cb_input_device_init(self):
        """
        Initialize input device combobox

        Will check previous options and set to default if not available.
        If default is not available, will show a warning.
        """
        success, host_detail = get_default_host_api()
        if success:
            assert isinstance(host_detail, Dict)
            defaultHost = str(host_detail["name"])
        else:
            defaultHost = ""

        self.cb_hostAPI["values"] = get_host_apis()
        self.cb_device["values"] = get_input_devices(defaultHost)

        # Setting previous options
        if sj.cache["hostAPI"] not in self.cb_hostAPI["values"]:
            self.hostAPI_set_default(onInit=True)
        else:
            self.cb_hostAPI.set(sj.cache["hostAPI"])

        # if the previous mic is not available, set to default
        if sj.cache["device"] not in self.cb_device["values"]:
            self.device_set_default()
        else:
            self.cb_device.set(sj.cache["device"])

    def input_device_menu(self, theType: Literal["hostAPI", "device"]):
        """
        Return a menu for input device combobox

        Args:
            theType (Literal["hostAPI", "device"]): The type of the combobox

        Returns:
            List[str]: A list of menu items
        """
        refreshDict = {
            "hostAPI": self.hostAPI_refresh,
            "device": self.device_refresh,
        }

        setDefaultDict = {
            "hostAPI": self.hostAPI_set_default,
            "device": self.device_set_default,
        }

        getDefaultDict = {
            "hostAPI": get_default_host_api,
            "device": get_default_input_device,
        }

        menu = Menu(self.btn_config_hostAPI, tearoff=0)
        menu.add_command(label="Refresh", command=refreshDict[theType])
        menu.add_command(label="Set to default", command=setDefaultDict[theType])

        success, default_host = getDefaultDict[theType]()
        if success:
            assert isinstance(default_host, Dict)
            menu.add_separator()
            menu.add_command(label=f"Default: {default_host['name']}", state="disabled")

        return menu

    def hostAPI_change(self, _event=None):
        self.cb_device["values"] = get_input_devices(self.cb_hostAPI.get())

        # search for the device in the list
        prevName = self.cb_device.get().split("|")[1].strip()
        found, index = False, 0
        for i, device in enumerate(self.cb_device["values"]):
            if prevName in device:
                found, index = True, i
                break

        if found:
            self.cb_device.current(index)
        else:
            self.cb_device.current(0)

    def hostAPI_refresh(self, _event=None):
        self.cb_hostAPI["values"] = get_host_apis()
        # verify if the current hostAPI is still available
        if self.cb_hostAPI.get() not in self.cb_hostAPI["values"]:
            self.cb_hostAPI.current(0)

        self.menu_hostAPI = self.input_device_menu("hostAPI")

    def hostAPI_set_default(self, _event=None, onInit=False):
        """
        Set hostAPI to default. Will update the list first.
        -> Show warning error if no default hostAPI found
        -> Set to default hostAPI if found, but will set to the first hostAPI if the default hostAPI is not available
        """
        self.hostAPI_refresh()  # update list
        success, default_host = get_default_host_api()
        if not success:
            nativeNotify("Error", str(default_host))
            self.cb_hostAPI.set("[ERROR] Getting default hostAPI failed")
        else:
            assert isinstance(default_host, Dict)
            if default_host["name"] not in self.cb_hostAPI["values"]:
                logger.warning(f"Default hostAPI {default_host['name']} not found, set to {self.cb_hostAPI['values'][0]}")
                self.cb_hostAPI.current(0)
            else:
                self.cb_hostAPI.set(default_host["name"])
            sj.save_key("hostAPI", self.cb_hostAPI.get())

        if not onInit:
            self.hostAPI_change()

    def device_refresh(self, _event=None):
        self.cb_device["values"] = get_input_devices(self.cb_hostAPI.get())
        if self.cb_device.get() not in self.cb_device["values"]:
            self.cb_device.current(0)

        self.menu_device = self.input_device_menu("device")

    def device_set_default(self, _event=None):
        """
        Set mic device to default. Will update the list first.
        -> Show warning error if no default mic found
        -> Will search from the currently updated list and set it to the first mic if the default mic is not available
        """
        self.device_refresh()  # update list
        success, default_device = get_default_input_device()
        if not success:
            nativeNotify("Error", str(default_device))
            self.cb_device.set("[WARNING] No default mic found")
        else:
            assert isinstance(default_device, Dict)
            found = False
            index = 0
            for i, name in enumerate(self.cb_device["values"]):
                if similar(default_device["name"], name) > 0.6:
                    found = True
                    index = i
                    break

            if not found:
                logger.warning(f"Default mic {default_device['name']} not found, set to {self.cb_device['values'][0]}")
                self.cb_device.current(0)
            else:
                self.cb_device.set(self.cb_device["values"][index])
            sj.save_key("device", self.cb_device.get())

    def vad_mode_change(self, value=None):
        get = self.cb_vad_mode.get()
        sj.save_key("vad_mode", get)
        if get != "Off":
            self.vad.set_mode(int(get))

        self.lbl_vad_status["text"] = "VAD: Off" if get == "Off" else "VAD: On"

    def slider_beeper_move(self, event):
        """
        When the slider is moved
        """
        self.lbl_beep_when_value["text"] = f"{float(event):.2f} db"
        self.audio_meter.set_threshold(float(event))
        self.audio_meter.meter_update()

    def init_mixer_with_check(self):
        try:
            if mixer.get_init() is None:
                logger.debug("Initializing mixer...")
                music_file = sj.cache["custom_beep_path"] if sj.cache["custom_beep_path"] != "" else beep_default
                mixer.init()
                mixer.music.load(music_file)
        except Exception as e:
            logger.exception(e)

    def quit_mixer(self):
        try:
            mixer.quit()
        except Exception as e:
            logger.exception(e)

    def play_sound(self):
        try:
            mixer.music.set_volume(sj.cache["beep_volume"] / 100)
            mixer.music.play(start=0.1)

        except Exception as e:
            logger.exception(e)

    def close_hush_meter(self):
        self.streaming = False
        self.lbl_vad_status["text"] = "VAD: Off" if sj.cache["vad_mode"] == "Off" else "VAD: On"
        # STOP
        self.btn_toggle_start_hush["text"] = "Start"
        self.cb_device["state"] = "readonly"
        self.cb_hostAPI["state"] = "readonly"
        self.cb_sample_rate["state"] = "readonly"
        self.cb_channel["state"] = "readonly"

        self.audio_meter.set_db(MIN_THRESHOLD)
        self.audio_meter.stop()
        try:
            if self.stream_rec:
                self.stream_rec.stop_stream()
                self.stream_rec.close()
                self.stream_rec = None

            if self.p_rec:
                self.p_rec.terminate()
                self.p_rec = None
        except Exception as e:
            logger.exception(e)

    def hush_meter(self, in_data, frame_count, time_info, status):
        assert self.detail_device is not None
        db = get_db(in_data)
        self.audio_meter.set_db(db)

        if db > self.max_v:
            self.max_v = db
            self.audio_meter.max = db
        elif db < self.min_v:
            self.min_v = db
            self.audio_meter.min = db

        if sj.cache["vad_mode"] != "off":
            self.is_speech = self.vad.is_speech(in_data, self.detail_device["sample_rate"])
            if self.is_speech:
                self.lbl_vad_status["text"] = "VAD: On - Speaking"
            else:
                self.lbl_vad_status["text"] = "VAD: On - Not speaking"

        if db < sj.cache["beep_when_reach"]:
            return (in_data, pyaudio.paContinue)

        if sj.cache["vad_mode"] == "off":
            self.play_sound()
            return (in_data, pyaudio.paContinue)

        if self.is_speech:
            self.play_sound()

        return (in_data, pyaudio.paContinue)

    def call_hush_meter(self, start):
        try:
            # must be enable and not in auto mode
            if start:
                # START
                self.btn_toggle_start_hush["text"] = "Stop"
                self.cb_device["state"] = "disabled"
                self.cb_hostAPI["state"] = "disabled"
                self.cb_sample_rate["state"] = "disabled"
                self.cb_channel["state"] = "disabled"

                self.max_v = MAX_THRESHOLD
                self.min_v = MIN_THRESHOLD
                self.p_rec = pyaudio.PyAudio()
                self.audio_meter.set_threshold(sj.cache["beep_when_reach"])
                logger.debug("getting device details")
                success, detail = get_device_details(sj, self.p_rec)
                if success:
                    self.detail_device = detail
                else:
                    raise Exception("Failed to get mic device details")

                self.init_mixer_with_check()
                self.stream_rec = self.p_rec.open(
                    format=pyaudio.paInt16,
                    channels=get_channel_int(self.detail_device["num_of_channels"]),
                    rate=self.detail_device["sample_rate"],
                    input=True,
                    frames_per_buffer=self.detail_device["chunk_size"],
                    input_device_index=self.detail_device["device_detail"]["index"],  # type: ignore
                    stream_callback=self.hush_meter,
                )

                self.audio_meter.start()
                self.streaming = True
            else:
                self.close_hush_meter()
        except Exception as e:
            logger.exception(e)
            # fail because probably no device
            self.close_hush_meter()
            nativeNotify("Error", "Failed to start mic meter. Check log for more details")

    def start_hush(self):
        t_meter = Thread(target=self.call_hush_meter, daemon=True, args=[self.btn_toggle_start_hush["text"] == "Start"])
        t_meter.start()

    # ----------------------------------------------------------------------
    def open_dl_link(self, _event=None):
        OpenUrl("https://github.com/Dadangdut33/Hush/releases/tag/latest")

    def check_for_update(self, _event=None, onStart=False):
        if self.checking:
            return

        self.checking = True
        self.update_fg = "black"
        self.tooltip_version.text = "Checking... Please wait"
        self.lbl_version.configure(foreground=self.update_fg)
        self.root.update()
        logger.info("Checking for update...")

        Thread(target=self.req_update_check, daemon=True).start()

    def req_update_check(self):
        try:
            # request to github api, compare version. If not same tell user to update
            req = get("https://api.github.com/repos/Dadangdut33/Hush/releases/latest")

            if req is not None and req.status_code == 200:
                data = req.json()
                latest_version = str(data["tag_name"])
                if __version__ < latest_version:
                    logger.info(f"New version found: {latest_version}")
                    self.update_fg = "blue"
                    self.update_func = self.open_dl_link
                    self.tooltip_version.text = "New version available. Click to go to the latest release page"
                    nativeNotify("New version available", "Visit the repository to download the latest update")
                else:
                    logger.info("No update available")
                    self.update_fg = "green"
                    self.update_func = self.check_for_update
                    self.tooltip_version.text = "You are using the latest version"
            else:
                logger.warning("Failed to check for update")
                self.update_fg = "red"
                self.update_func = self.check_for_update
                self.tooltip_version.text = "Fail to check for version update, click to try again"

            self.lbl_version.configure(foreground=self.update_fg)
            self.lbl_version.bind("<Button-1>", self.update_func)

            self.checking = False
        except Exception as e:
            logger.exception(e)
            self.update_fg = "red"
            self.update_func = self.check_for_update
            self.tooltip_version.text = "Fail to check for version update, click to try again"
            self.lbl_version.configure(foreground=self.update_fg)
            self.lbl_version.bind("<Button-1>", self.update_func)
        finally:
            self.checking = False


def main():
    logger.info(f"Starting {APP_NAME} {__version__}")

    tray = AppTray()  # noqa
    main = Hush()
    main.root.mainloop()

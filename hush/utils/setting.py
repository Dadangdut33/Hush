__all__ = ["default_setting", "SettingJson"]
import json
from os import makedirs, path
from typing import List

from notifypy import Notify

from hush._version import __setting_version__
from hush.components.message import mbox
from hush.custom_logging import logger

default_setting = {
    "version": __setting_version__,
    "checkUpdateOnStart": True,
    "keep_log": False,
    # ------------------ #
    "hostAPI": "",
    "device": "",
    "sample_rate": "16000",  # 8000, 16000, 32000, 48000
    "channel": "Mono",  # Mono, Stereo
    "vad_mode": "2",  # Off, 1, 2, 3
    "custom_beep_path": "",
    "beep_volume": 80,
    "beep_when_reach": -8.0,  # db
    "mw_size": "500x250",
}


class SettingJson:
    """
    Class to handle setting.json
    """
    def __init__(self, setting_path: str, setting_dir: str, checkdirs: List[str]):
        self.cache = {}
        self.setting_path = setting_path
        self.dir = setting_dir
        self.createDirectoryIfNotExist(self.dir)  # setting dir
        for checkdir in checkdirs:
            self.createDirectoryIfNotExist(checkdir)
        self.createDefaultSettingIfNotExist()  # setting file

        # Load setting
        success, msg, data = self.loadSetting()
        if success:
            self.cache = data
            # verify loaded setting
            success, msg, data = self.verifyLoadedSetting(data)
            if not success:
                self.cache = default_setting
                notification = Notify()
                notification.application_name = "Hush"
                notification.title = "Error: Verifying setting file"
                notification.message = "Setting reverted to default. Details: " + msg
                notification.send()
                logger.warning("Error verifying setting file: " + msg)

            # verify setting version
            if self.cache["version"] != __setting_version__:
                # save old one as backup
                self.save_old_setting(self.cache)
                self.cache = default_setting  # load default
                self.save(self.cache)  # save
                notification = Notify()
                notification.application_name = "Hush"
                notification.title = "Setting file is outdated"
                notification.message = "Setting file is outdated. Setting has been reverted to default setting."
                notification.send()
                logger.warning(
                    "Setting file is outdated. Setting has been reverted to default setting. "
                    "You can find your old setting in the user folder."
                )

            logger.info("Setting loaded")
        else:
            self.cache = default_setting
            logger.error("Error loading setting file: " + msg)
            mbox("Error", "Error: Loading setting file. " + self.setting_path + "\nReason: " + msg, 2)

    def createDirectoryIfNotExist(self, dir: str):
        """
        Create directory if it doesn't exist
        """
        try:
            if not path.exists(dir):
                makedirs(dir)
        except Exception as e:
            mbox("Error", "Error: Creating directory. " + dir + "\nReason: " + str(e), 2)

    def createDefaultSettingIfNotExist(self):
        """
        Create default json file if it doesn't exist
        """
        setting_path = self.setting_path
        try:
            if not path.exists(setting_path):
                with open(setting_path, "w", encoding="utf-8") as f:
                    json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception(e)
            mbox("Error", "Error: Creating default setting file. " + setting_path + "\nReason: " + str(e), 2)

    def createDefaultSetting(self):
        """
        Create default json file
        """
        setting_path = self.setting_path
        try:
            with open(setting_path, "w", encoding="utf-8") as f:
                json.dump(default_setting, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.exception(e)
            mbox("Error", "Error: Creating default setting file. " + setting_path + "\nReason: " + str(e), 2)

    def save(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(self.setting_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
            self.cache = data
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def save_cache(self):
        """
        Save but from cache
        """
        return self.save(self.cache)

    def save_old_setting(self, data: dict):
        """
        Save json file
        """
        success: bool = False
        msg: str = ""
        try:
            with open(
                self.setting_path.replace("setting.json", f"setting_old_{data['version']}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg

    def save_key(self, key: str, value):
        """
        Save only a part of the setting
        """
        if key not in self.cache:
            logger.error("Error saving setting: " + key + " not in cache")
            return
        if self.cache[key] == value:  # if same value
            return

        self.cache[key] = value
        success, msg = self.save(self.cache)

        if not success:
            notification = Notify()
            notification.application_name = "Hush"
            notification.title = "Error: Saving setting file"
            notification.message = "Reason: " + msg
            notification.send()
            logger.error("Error saving setting file: " + msg)

    def loadSetting(self):
        """
        Load json file
        """
        success: bool = False
        msg: str = ""
        data: dict = {}
        try:
            with open(self.setting_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def verifyLoadedSetting(self, data: dict):
        """
        Verify loaded setting
        """
        success: bool = False
        msg: str = ""
        try:
            # check each key
            for key in default_setting:
                if key not in data:
                    data[key] = default_setting[key]

            success = True
        except Exception as e:
            msg = str(e)
        finally:
            return success, msg, data

    def getSetting(self):
        """
        Get setting value
        """
        return self.cache

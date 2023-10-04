import os
from ._path import dir_log, dir_user
from .utils.setting import SettingJson
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .app import AppTray, Hush

sj: SettingJson = SettingJson(os.path.join(dir_user, "setting.json"), dir_user, [dir_log])


class GlobalClass:
    def __init__(self):
        self.running = True
        self.running_after_id = ""
        self.tray: Optional[AppTray] = None
        self.mw: Optional[Hush] = None


gc = GlobalClass()

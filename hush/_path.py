import os

# Paths
dir_project: str = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
dir_user: str = os.path.abspath(os.path.join(dir_project, "user"))
dir_theme: str = os.path.abspath(os.path.join(dir_project, "theme"))
dir_setting: str = os.path.abspath(os.path.join(dir_project, "setting"))
dir_log: str = os.path.abspath(os.path.join(dir_project, "log"))
dir_assets: str = os.path.abspath(os.path.join(dir_project, "assets"))
app_icon: str = os.path.abspath(os.path.join(dir_assets, "icon.ico"))
beep_default: str = os.path.abspath(os.path.join(dir_assets, "beep.mp3"))

# verify app_icon exist or not
if not os.path.exists(app_icon):
    app_icon_missing = True
else:
    app_icon_missing = False

import sys
from cx_Freeze import setup, Executable

build_exe_options = {"excludes": ["unittest"], "build_exe": "build/Hush"}

bdist_msi_options = {
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\%s" % ("Hush"),
    "install_icon": "hush/assets/icon.ico",
    "product_code": "{88DB5BD9-0C7F-4438-97F2-01EFED1A7AED}",
    "upgrade_code": "{79B0E008-56A4-437B-BA71-611B202BD51F}",
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Hush",
    version="1.0.0",
    description="A simple app that notifies you to be silence by beeping when you are too loud",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=[Executable("Run.py", base=base, icon="hush/assets/icon.ico", target_name="Hush.exe")],
)

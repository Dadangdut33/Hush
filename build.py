import sys
import os
from cx_Freeze import setup, Executable


def version():
    with open(os.path.join(os.path.dirname(__file__), "hush/_version.py")) as f:
        return f.readline().split("=")[1].strip().strip('"').strip("'")


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
    version=version(),
    description="A simple app that notifies you to be silence by beeping when you are too loud",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=[Executable("Run.py", base=base, icon="hush/assets/icon.ico", target_name="Hush.exe")],
)

print("Copying files...")
# copy Lincese as license.txt to build/Hush
with open("LICENSE", "r", encoding="utf-8") as f:
    with open("build/Hush/license.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# copy README.md as README.txt to build/Hush
with open("README.md", "r", encoding="utf-8") as f:
    with open("build/Hush/README.txt", "w", encoding="utf-8") as f2:
        f2.write(f.read())

# create version.txt
with open("build/Hush/version.txt", "w", encoding="utf-8") as f:
    f.write(version())

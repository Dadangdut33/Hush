<p align="center">
    <img src="https://raw.githubusercontent.com/Dadangdut33/Hush/master/hush/assets/logo.jpeg" width="300px" alt="Hush Logo / icon">
</p>

<h1 align="center">Hush</h1>

<p align="center">
    <a href="https://github.com/Dadangdut33/Hush/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/Dadangdut33/Hush"></a>
    <a href="https://github.com/Dadangdut33/Hush/pulls"><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Dadangdut33/Hush"></a>
    <a href="https://github.com/Dadangdut33/Hush/releases/latest"><img alt="github downloads"  src="https://img.shields.io/github/downloads/Dadangdut33/Hush/total?label=downloads (github)"></a> 
    <a href="https://github.com/Dadangdut33/Hush/releases/latest"><img alt="GitHub release (latest SemVer)" src="https://img.shields.io/github/v/release/Dadangdut33/Hush"></a>
    <a href="https://github.com/Dadangdut33/Hush/commits/main"><img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/Dadangdut33/Hush/latest"></a><Br>
    <a href="https://github.com/Dadangdut33/Hush/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Dadangdut33/Hush?style=social"></a>
    <a href="https://github.com/Dadangdut33/Hush/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/Dadangdut33/Hush?style=social"></a>
</p>

"Hush" is your trusty companion for those moments when you need to embrace the silence, but you find yourself lost in the captivating world of gaming. Picture this: you're deeply engrossed in an intense gaming session, completely oblivious to the outside world. Little do you know, your excitement is echoing through your space, and suddenly, a gentle knock on the door reminds you that your neighbor or housemate kindly requests a moment of tranquility. That's where "Hush" comes to the rescue! This app will let you know that you are too loud by beeping, it's your subtle yet effective mic loudness notifier, ensuring you stay in the good graces of those around you while you continue to conquer the virtual realm. Don't let noise disturbances be your downfall; let "Hush" be your secret weapon for serenity.

In short, Hush is a simple app that notifies you when you are too loud. It does this by monitoring your microphone input and notifying you when you are too loud by beeping.

<details open>
    <summary>Preview</summary>
    <p align="center">
        <img src="https://raw.githubusercontent.com/Dadangdut33/Hush/master/hush/assets/preview.png" width="700" alt="Hush preview">
    </p>
</details>


# Table of Contents

- [About Hush](#Hush)
- [Install](#install)
  - [Install pre compiled version](#install-pre-compiled-version)
  - [Install as a module](#install-as-a-module)
- [Uninstall](#uninstall)
- [Building / Developing / Compiling Yourself](#building--developing--compiling-yourself)
- [Attribution](#attribution)

# Install

To install, you can choose either the pre compiled version or as a module through pip.

## Install pre compiled version

1. Download the [latest release](https://github.com/Dadangdut33/Hush/releases/latest) (Choose either installer or portable)
2. Install / Extract the downloaded file
3. Run the executable
4. Enjoy!

## Install as a module

> [!NOTE]  
> If you want to install from a specific branch or commit, you can do it by adding `@branch_name` or `@commit_hash` at the end of the url

> [!IMPORTANT]  
> If you are updating from an older version, you need to add `--upgrade --no-deps --force-reinstall` at the end of the command.

```bash
pip install -U git+https://github.com/Dadangdut33/Hush.git
```

# Uninstall

If you are using the installer version, you can run the uninstaller. If you are using the portable version, you can just delete the folder. If you are using the module version, you can run `pip uninstall hush`.

# Building / Developing / Compiling Yourself

> [!NOTE]  
> I use python 3.10.11 for development, but it should work on any python 3.8+ version.

## Prerequisites

1. Clone the repo
2. Install the dependencies using `pip install -r requirements.txt`
3. Check that the dependencies are installed correctly by running `python -m hush` or `python run.py` (You should see the GUI pop up)

## Building

The app is build using cx_freeze. To build, run `python build.py build_exe`. The built app will be in the `build` folder. To make the installer, you can also run `python build.py bdist_msi` but this is limited so i use [inno setup](https://jrsoftware.org/isinfo.php) with the script located in [./installer.iss]

# Attribution

The logo is AI generated using Dall-e 3.

The beep sound is from [here](https://sound-searcher.com/sound.php?id=426).

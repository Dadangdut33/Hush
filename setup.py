import os
from setuptools import setup


def version():
    with open(os.path.join(os.path.dirname(__file__), "hush/_version.py")) as f:
        return f.readline().split("=")[1].strip().strip('"').strip("'")


def read_me():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


def install_requires():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        req = f.read().splitlines()
        return req


setup(
    name="Hush",
    version=version(),
    description="A simple app that notifies you to be silence by beeping when you are too loud",
    long_description=read_me(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    author="Dadangdut33",
    url="https://github.com/Dadangdut33/Hush",
    license="MIT",
    packages=["hush", "hush.utils", "hush.utils.audio", "hush.components", "hush.assets"],
    package_data={"hush.assets": ["*"]},
    install_requires=install_requires(),
    entry_points={"console_scripts": ["hush=hush.__main__:main"]},
    include_package_data=True,
)

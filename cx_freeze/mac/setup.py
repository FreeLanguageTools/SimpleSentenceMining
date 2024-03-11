import sys
from vocabsieve import __version__
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
include_files = [
    ('../../vocabsieve/reader/templates/',
     'lib/vocabsieve/reader/templates/'),
    ('../../vocabsieve/reader/static/',
     'lib/vocabsieve/reader/static/')] 

build_exe_options = {
    "includes": [
        "vocabsieve",
        "setuptools",
        "PyQt5",
        "bs4",
        "lxml",
        "simplemma",
        "pyqtgraph",
        "qdarktheme",
        "bidict",
        "pystardict",
        "flask",
        "pymorphy3",
        "pymorphy3_dicts_ru",
        "pymorphy3_dicts_uk",
        "jinja2.ext",
        "sqlite3",
        "charset_normalizer",
        "slpp",
        "ebooklib",
        "markdown",
        "markdownify",
        "lzo",
        "readmdict",
        "requests",
        "packaging",
        "pynput",
        "pynput.keyboard._darwin",
        "pynput.mouse._darwin",
        "gevent"
        ],
    "include_files": include_files,
    "excludes": ["tkinter"],
    "include_msvcr": True,
    "silent_level": 1
    }

bdist_mac_options = {
    'iconfile': "../icon.icns",
    'bundle_name': f"VocabSieve-v{__version__}-macos",
    'custom_info_plist': '../Info.plist',
}

bdist_dmg_options = {
    'volume_label': f"VocabSieve-v{__version__}-macos",
    'applications_shortcut': True,

}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(
    name="VocabSieve",
    version=__version__,
    description="A simple sentence mining tool",
    options={"build_exe": build_exe_options, "bdist_mac": bdist_mac_options, "bdist_dmg": bdist_dmg_options},
    executables=[Executable("app.py",
                            base=base,
                            icon="../icon.ico",
                            shortcut_name="VocabSieve",
                            shortcut_dir="DesktopFolder")]
)

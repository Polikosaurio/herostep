# paths.py — resolución centralizada de rutas para dev y build .exe (PyInstaller)
#
# En desarrollo:  BASE_DIR = carpeta del script
# En .exe:        assets y locales vienen de sys._MEIPASS (bundle de solo lectura)
#                 datos de usuario (scores.json) van a %APPDATA%/HeroStep/

import os
import sys

APP_NAME = "HeroStep"


def _bundle_dir() -> str:
    """Raíz del bundle en .exe, o directorio del script en desarrollo."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _appdata_dir() -> str:
    """Carpeta de datos de usuario persistentes (escritura). %APPDATA%/HeroStep en Windows."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(base, APP_NAME)


# ── Rutas de solo lectura (assets, locales) ───────────────────────────────────

def asset_chars_dir() -> str:
    return os.path.join(_bundle_dir(), "assets", "chars")

def asset_steps_dir() -> str:
    return os.path.join(_bundle_dir(), "assets", "steps")

def locales_dir() -> str:
    return os.path.join(_bundle_dir(), "locales")

def locale_file(lang_code: str) -> str:
    return os.path.join(locales_dir(), f"{lang_code}.json")


# ── Rutas de escritura (datos de usuario) ─────────────────────────────────────

def userdata_dir() -> str:
    path = _appdata_dir()
    os.makedirs(path, exist_ok=True)
    return path

def scores_file() -> str:
    return os.path.join(userdata_dir(), "scores.json")

def settings_file() -> str:
    return os.path.join(userdata_dir(), "settings.json")


# ── Utilidad de diagnóstico ───────────────────────────────────────────────────

def debug_info() -> dict:
    return {
        "frozen":       getattr(sys, "frozen", False),
        "bundle_dir":   _bundle_dir(),
        "appdata_dir":  _appdata_dir(),
        "scores_file":  scores_file(),
    }

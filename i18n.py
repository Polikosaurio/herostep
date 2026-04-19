# i18n.py — carga y acceso a strings localizados
#
# Uso:
#   from i18n import t, set_lang
#   set_lang("es")
#   label = t("summary.title")
#   label = t("statusbar.correct", n=5)

import json
import os
from typing import Any
from paths import locale_file

_strings: dict = {}
_lang_code: str = "en"
DEFAULT_LANG = "en"


def set_lang(lang_code: str) -> None:
    global _strings, _lang_code
    path = locale_file(lang_code)
    if not os.path.exists(path):
        if lang_code != DEFAULT_LANG:
            set_lang(DEFAULT_LANG)   # fallback silencioso a inglés
        return
    with open(path, "r", encoding="utf-8") as f:
        _strings = json.load(f)
    _lang_code = lang_code


def t(key: str, **kwargs: Any) -> str:
    """
    Accede a una clave anidada con notación de punto.
    Ejemplo: t("summary.hits", correct=7, total=10)
    Si la clave no existe, devuelve la propia clave como fallback visible.
    """
    parts = key.split(".")
    node = _strings
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return key   # fallback visible: muestra la clave, nunca rompe
    if not isinstance(node, str):
        return key
    if kwargs:
        try:
            return node.format(**kwargs)
        except KeyError:
            return node
    return node


def current_lang() -> str:
    return _lang_code


def load_lang_setting() -> str:
    from paths import settings_file
    import os
    path = settings_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("lang", DEFAULT_LANG)
        except Exception:
            pass
    return DEFAULT_LANG

def save_lang_setting(lang_code: str) -> None:
    from paths import settings_file
    with open(settings_file(), "w", encoding="utf-8") as f:
        json.dump({"lang": lang_code}, f)

set_lang(load_lang_setting() or DEFAULT_LANG)

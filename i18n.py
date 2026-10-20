"""Lokalizacja (i18n) Island Defenders - fala 1: EN, PL, DE, ES, FR, PT-BR, RU.

Zasady:
- Angielski jest jezykiem zrodlowym i zawsze kompletny (lang/en.json).
- t(key, default) zwraca tlumaczenie dla biezacego jezyka; gdy brakuje
  klucza, spada na angielski, potem na `default`, na koncu na sam klucz.
- Wybor jezyka zapisuje sie w language.json (ten sam wzorzec co
  resolution.json) i obowiazuje od razu w menu glownym; gre (Game)
  tworzy sie juz po wyborze, wiec jej teksty tez sa w wybranym jezyku.
- Nazwy wrogow i nazwy wlasne (Bonnie, Clyde) sie nie tlumaczy.
"""
import json
import os

# Kolejnosc = kolejnosc flag w menu glownym. (kod, autonazwa, plik flagi)
LANGUAGES = [
    ("en", "English", "gb"),
    ("pl", "Polski", "pl"),
    ("de", "Deutsch", "de"),
    ("es", "Español", "es"),
    ("fr", "Français", "fr"),
    ("pt", "Português (Brasil)", "br"),
    ("ru", "Русский", "ru"),
]
LANG_CODES = [code for code, _, _ in LANGUAGES]
LANG_NAMES = {code: name for code, name, _ in LANGUAGES}
LANG_FLAGS = {code: flag for code, _, flag in LANGUAGES}

_DIR = os.path.dirname(os.path.abspath(__file__))
_SAVE_FILE = os.path.join(_DIR, "language.json")

_strings = {}   # code -> {key: text}
_current = "en"


def _load_file(code):
    path = os.path.join(_DIR, "lang", code + ".json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _load_all():
    for code in LANG_CODES:
        _strings[code] = _load_file(code)


def _load_choice():
    global _current
    try:
        if os.path.exists(_SAVE_FILE):
            with open(_SAVE_FILE, encoding="utf-8") as f:
                code = json.load(f).get("lang", "en")
            if code in LANG_CODES:
                _current = code
    except Exception:
        pass


def current():
    return _current


def set_language(code):
    """Przelacza jezyk i zapisuje wybor. Zwraca True gdy zmieniono."""
    global _current
    if code not in LANG_CODES or code == _current:
        return False
    _current = code
    try:
        with open(_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"lang": code}, f)
    except Exception:
        pass
    return True


def t(key, default=None, **fmt):
    """Tlumaczy klucz. Przyklady: t('menu.start'), t('hud.wave', n=3)."""
    text = None
    cur = _strings.get(_current, {})
    if key in cur:
        text = cur[key]
    elif key in _strings.get("en", {}):
        text = _strings["en"][key]
    if text is None:
        text = default if default is not None else key
    if fmt:
        try:
            text = text.format(**fmt)
        except Exception:
            pass
    return text


# Nazwy wiez po nazwie klasy (logika gry trzyma angielskie display_name,
# wyswietlanie tlumaczymy tutaj).
TOWER_NAME_KEYS = {
    "WoodenTower": "tower.wood",
    "MetalTower": "tower.metal",
    "GoldenTower": "tower.gold",
    "FireTower": "tower.fire",
    "BlazeTower": "tower.blaze",
    "SpikeCluster": "tower.spikes",
}
TOWER_SHORT_KEYS = {
    "Wood": "tower.wood_short",
    "Metal": "tower.metal_short",
    "Golden": "tower.gold_short",
    "Gold": "tower.gold_short",
    "Fire": "tower.fire_short",
    "Blaze": "tower.blaze_short",
}
ABILITY_KEYS = {
    "Wood": "ability.wood",
    "Metal": "ability.metal",
    "Gold": "ability.gold",
    "Fire": "ability.fire",
    "Blaze": "ability.blaze",
}


def tower_name(cls_name, default=None):
    key = TOWER_NAME_KEYS.get(cls_name)
    return t(key, default) if key else (default or cls_name)


_load_all()
_load_choice()

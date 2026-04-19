# roster.py
# Orden oficial del roster de Overwatch 2 + héroes nuevos
# Nombres en minúsculas, sin espacios, sin caracteres especiales
# Debe coincidir exactamente con los archivos en assets/chars/ y assets/steps/

ROSTER = [
    # ── TANKS (14) ──────────────────────────────────────────────
    {"name": "dva",          "role": "tank"},
    {"name": "doomfist",     "role": "tank"},
    {"name": "domina",       "role": "tank"},
    {"name": "hazard",       "role": "tank"},
    {"name": "junkerqueen",  "role": "tank"},
    {"name": "mauga",        "role": "tank"},
    {"name": "orisa",        "role": "tank"},
    {"name": "ramattra",     "role": "tank"},
    {"name": "reinhardt",    "role": "tank"},
    {"name": "roadhog",      "role": "tank"},
    {"name": "sigma",        "role": "tank"},
    {"name": "winston",      "role": "tank"},
    {"name": "wreckingball", "role": "tank"},
    {"name": "zarya",        "role": "tank"},

    # ── DAMAGE (23) ─────────────────────────────────────────────
    {"name": "anran",        "role": "damage"},
    {"name": "ashe",         "role": "damage"},
    {"name": "bastion",      "role": "damage"},
    {"name": "cassidy",      "role": "damage"},
    {"name": "echo",    "role": "damage"},
    {"name": "emre",         "role": "damage"},
    {"name": "freja",        "role": "damage"},
    {"name": "genji",        "role": "damage"},
    {"name": "hanzo",        "role": "damage"},
    {"name": "junkrat",      "role": "damage"},
    {"name": "mei",          "role": "damage"},
    {"name": "pharah",       "role": "damage"},
    {"name": "reaper",       "role": "damage"},
    {"name": "sierra",       "role": "damage"},
    {"name": "sojourn",      "role": "damage"},
    {"name": "soldier76",    "role": "damage"},
    {"name": "sombra",       "role": "damage"},
    {"name": "symmetra",     "role": "damage"},
    {"name": "torbjorn",     "role": "damage"},
    {"name": "tracer",       "role": "damage"},
    {"name": "vendetta",     "role": "damage"},
    {"name": "venture",      "role": "damage"},
    {"name": "widowmaker",   "role": "damage"},

    # ── SUPPORT (15) ────────────────────────────────────────────
    {"name": "ana",          "role": "support"},
    {"name": "baptiste",     "role": "support"},
    {"name": "brigitte",     "role": "support"},
    {"name": "illari",       "role": "support"},
    {"name": "jetpackcat",   "role": "support"},
    {"name": "juno",         "role": "support"},
    {"name": "kiriko",       "role": "support"},
    {"name": "lifeweaver",   "role": "support"},
    {"name": "lucio",        "role": "support"},
    {"name": "mercy",        "role": "support"},
    {"name": "mizuki",       "role": "support"},
    {"name": "moira",        "role": "support"},
    {"name": "wuyang",       "role": "support"},
    {"name": "zenyatta",     "role": "support"},
]

# Colores por rol (RGB) — usados en el grid para separadores y highlights
ROLE_COLORS = {
    "tank":    (70,  130, 220),
    "damage":  (210,  60,  60),
    "support": (60,  190,  90),
}

ROLE_ORDER = ["tank", "damage", "support"]

ROLE_LABELS = {
    "tank":    "TANK",
    "damage":  "DAMAGE",
    "support": "SUPPORT",
}


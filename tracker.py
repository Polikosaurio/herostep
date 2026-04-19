# tracker.py — sistema de pesos silencioso y persistencia de sesión

import json
import os
import random
from roster import ROSTER
from paths import scores_file

DEFAULT_WEIGHT  = 100.0
MIN_WEIGHT      =  10.0
WEIGHT_TIME_GAIN  = 1.0    # peso ganado por segundo escuchando sin acertar
WEIGHT_HIT_FAST   = 0.85   # multiplicador al acertar rápido (< 3s)
WEIGHT_HIT_SLOW   = 0.95   # multiplicador al acertar lento  (>= 3s)


def _default_entry() -> dict:
    return {"weight": DEFAULT_WEIGHT, "hits": 0, "misses": 0, "total_time": 0.0}


def load_data() -> dict:
    path = scores_file()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    # Asegurar que todos los héroes del roster tienen entrada
    for hero in ROSTER:
        data.setdefault(hero["name"], _default_entry())
    return data


def save_data(data: dict) -> None:
    path = scores_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def reset_data() -> dict:
    """Borra todas las estadísticas y devuelve datos limpios."""
    fresh = {hero["name"]: _default_entry() for hero in ROSTER}
    save_data(fresh)
    return fresh


def pick_hero(data: dict, available_names: list[str]) -> str:
    """Weighted random: más peso = más probable de salir."""
    weights = [max(data.get(n, _default_entry())["weight"], MIN_WEIGHT)
               for n in available_names]
    return random.choices(available_names, weights=weights, k=1)[0]


def on_correct(data: dict, name: str, elapsed: float) -> None:
    """Reduce el peso del héroe según velocidad de respuesta."""
    entry  = data.setdefault(name, _default_entry())
    factor = WEIGHT_HIT_FAST if elapsed < 3.0 else WEIGHT_HIT_SLOW
    entry["weight"]     = max(entry["weight"] * factor, MIN_WEIGHT)
    entry["hits"]      += 1
    entry["total_time"] += elapsed
    save_data(data)


def on_wrong(data: dict, name: str, elapsed: float) -> None:
    """Registra un fallo. El peso ya creció via tick_weight()."""
    entry = data.setdefault(name, _default_entry())
    entry["misses"]     += 1
    entry["total_time"] += elapsed
    save_data(data)


def tick_weight(data: dict, name: str, delta: float) -> None:
    """Llamado cada frame mientras el audio suena. Acumula dificultad."""
    entry = data.setdefault(name, _default_entry())
    entry["weight"] += WEIGHT_TIME_GAIN * delta


def get_summary(session_results: list[dict]) -> dict:
    """
    session_results: [{"name": str, "elapsed": float, "correct": bool}, ...]
    """
    total   = len(session_results)
    correct = sum(1 for r in session_results if r["correct"])
    avg_time = (sum(r["elapsed"] for r in session_results) / total) if total else 0.0
    hardest  = max(session_results, key=lambda r: r["elapsed"], default=None)
    return {
        "total":    total,
        "correct":  correct,
        "accuracy": round(correct / total * 100) if total else 0,
        "avg_time": round(avg_time, 1),
        "hardest":  hardest["name"] if hardest else None,
    }

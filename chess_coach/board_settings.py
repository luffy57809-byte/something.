# Keep these lists in sync with frontend/src/utils/boardThemes.js
THEMES = ["walnut", "green", "blue", "brown", "gray", "purple", "slate"]
HIGHLIGHTS = ["gold", "lime", "sky", "rose"]
ANIMATIONS = ["off", "fast", "normal", "slow"]
SIZES = ["small", "medium", "large"]

DEFAULTS = {
    "theme": "walnut",
    "highlight": "gold",
    "coordinates": True,
    "legalMoves": True,
    "animation": "normal",
    "size": "medium",
}


def normalize_settings(raw):
    """Keep only known keys with allowed values; fill everything else with defaults."""
    raw = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULTS)
    choices = {"theme": THEMES, "highlight": HIGHLIGHTS, "animation": ANIMATIONS, "size": SIZES}
    for key, allowed in choices.items():
        value = raw.get(key)
        if isinstance(value, str) and value in allowed:
            out[key] = value
    for key in ("coordinates", "legalMoves"):
        if isinstance(raw.get(key), bool):
            out[key] = raw[key]
    return out

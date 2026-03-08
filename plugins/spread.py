PLUGIN_NAME = "Spread"
PLUGIN_DESCRIPTION = "Randomly displace pixels for a frosted-glass effect"
PLUGIN_PARAMS = [
    {"name": "distance", "type": "float", "default": 5.0, "min": 1.0, "max": 50.0, "label": "Distance"},
]


def transform(image, params):
    distance = int(params.get("distance", 5))
    return image.effect_spread(distance)


def export_code(params):
    distance = int(params.get("distance", 5))
    return f"img = img.effect_spread({distance})"


def export_imports():
    return ""

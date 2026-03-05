PLUGIN_NAME = "Crop"
PLUGIN_DESCRIPTION = "Crop image by percentage from each edge"
PLUGIN_PARAMS = [
    {"name": "left", "type": "float", "default": 0.0, "min": 0.0, "max": 45.0, "label": "Left %", "step": 1.0},
    {"name": "top", "type": "float", "default": 0.0, "min": 0.0, "max": 45.0, "label": "Top %", "step": 1.0},
    {"name": "right", "type": "float", "default": 0.0, "min": 0.0, "max": 45.0, "label": "Right %", "step": 1.0},
    {"name": "bottom", "type": "float", "default": 0.0, "min": 0.0, "max": 45.0, "label": "Bottom %", "step": 1.0},
]


def transform(image, params):
    w, h = image.size
    left = int(w * params.get("left", 0.0) / 100.0)
    top = int(h * params.get("top", 0.0) / 100.0)
    right = w - int(w * params.get("right", 0.0) / 100.0)
    bottom = h - int(h * params.get("bottom", 0.0) / 100.0)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def export_code(params):
    left = params.get("left", 0.0)
    top = params.get("top", 0.0)
    right = params.get("right", 0.0)
    bottom = params.get("bottom", 0.0)
    return (
        f"w, h = img.size\n"
        f"img = img.crop((int(w*{left}/100), int(h*{top}/100), w-int(w*{right}/100), h-int(h*{bottom}/100)))"
    )


def export_imports():
    return ""

PLUGIN_NAME = "Pad"
PLUGIN_DESCRIPTION = "Resize image to fit within a target size, padding the remainder"
PLUGIN_PARAMS = [
    {"name": "width", "type": "float", "default": 800.0, "min": 16.0, "max": 8000.0, "label": "Target Width"},
    {"name": "height", "type": "float", "default": 600.0, "min": 16.0, "max": 8000.0, "label": "Target Height"},
    {"name": "fill_r", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Fill Red"},
    {"name": "fill_g", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Fill Green"},
    {"name": "fill_b", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Fill Blue"},
]


def transform(image, params):
    from PIL import ImageOps
    w = int(params.get("width", 800))
    h = int(params.get("height", 600))
    fill = (
        int(params.get("fill_r", 0)),
        int(params.get("fill_g", 0)),
        int(params.get("fill_b", 0)),
    )
    if image.mode == "RGBA":
        fill = fill + (255,)
    return ImageOps.pad(image, (w, h), color=fill)


def export_code(params):
    w = int(params.get("width", 800))
    h = int(params.get("height", 600))
    fill = (int(params.get("fill_r", 0)), int(params.get("fill_g", 0)), int(params.get("fill_b", 0)))
    return f"img = ImageOps.pad(img, ({w}, {h}), color={fill})"


def export_imports():
    return "from PIL import ImageOps"

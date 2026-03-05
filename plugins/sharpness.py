PLUGIN_NAME = "Sharpness"
PLUGIN_DESCRIPTION = "Adjust image sharpness"
PLUGIN_PARAMS = [
    {"name": "factor", "type": "float", "default": 1.0, "min": 0.0, "max": 3.0, "label": "Sharpness Factor"},
]


def transform(image, params):
    from PIL import ImageEnhance
    factor = params.get("factor", 1.0)
    return ImageEnhance.Sharpness(image).enhance(factor)


def export_code(params):
    factor = params.get("factor", 1.0)
    return f"img = ImageEnhance.Sharpness(img).enhance({factor})"


def export_imports():
    return "from PIL import ImageEnhance"

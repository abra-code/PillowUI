PLUGIN_NAME = "Smooth"
PLUGIN_DESCRIPTION = "Apply light smoothing to reduce noise"
PLUGIN_PARAMS = [
    {"name": "strong", "type": "bool", "default": False, "label": "Strong Smoothing"},
]


def transform(image, params):
    from PIL import ImageFilter
    if params.get("strong", False):
        return image.filter(ImageFilter.SMOOTH_MORE)
    return image.filter(ImageFilter.SMOOTH)


def export_code(params):
    if params.get("strong", False):
        return "img = img.filter(ImageFilter.SMOOTH_MORE)"
    return "img = img.filter(ImageFilter.SMOOTH)"


def export_imports():
    return "from PIL import ImageFilter"

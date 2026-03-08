PLUGIN_NAME = "Mode Filter"
PLUGIN_DESCRIPTION = "Replace each pixel with the most frequent value in its neighborhood"
PLUGIN_PARAMS = [
    {"name": "size", "type": "float", "default": 3.0, "min": 3.0, "max": 15.0, "step": 2.0, "label": "Window Size"},
]


def transform(image, params):
    from PIL import ImageFilter
    size = int(params.get("size", 3.0))
    if size % 2 == 0:
        size += 1
    return image.filter(ImageFilter.ModeFilter(size=size))


def export_code(params):
    size = int(params.get("size", 3.0))
    if size % 2 == 0:
        size += 1
    return f"img = img.filter(ImageFilter.ModeFilter(size={size}))"


def export_imports():
    return "from PIL import ImageFilter"

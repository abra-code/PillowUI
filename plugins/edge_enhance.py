PLUGIN_NAME = "Edge Enhance"
PLUGIN_DESCRIPTION = "Subtly enhance edges while preserving the image"
PLUGIN_PARAMS = [
    {"name": "strong", "type": "bool", "default": False, "label": "Strong Enhancement"},
]


def transform(image, params):
    from PIL import ImageFilter
    if params.get("strong", False):
        return image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return image.filter(ImageFilter.EDGE_ENHANCE)


def export_code(params):
    if params.get("strong", False):
        return "img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)"
    return "img = img.filter(ImageFilter.EDGE_ENHANCE)"


def export_imports():
    return "from PIL import ImageFilter"

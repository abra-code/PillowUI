PLUGIN_NAME = "Find Edges"
PLUGIN_DESCRIPTION = "Detect and highlight edges in the image"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageFilter
    return image.filter(ImageFilter.FIND_EDGES)


def export_code(params):
    return "img = img.filter(ImageFilter.FIND_EDGES)"


def export_imports():
    return "from PIL import ImageFilter"

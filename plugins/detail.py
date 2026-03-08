PLUGIN_NAME = "Detail"
PLUGIN_DESCRIPTION = "Enhance fine detail in the image"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageFilter
    return image.filter(ImageFilter.DETAIL)


def export_code(params):
    return "img = img.filter(ImageFilter.DETAIL)"


def export_imports():
    return "from PIL import ImageFilter"

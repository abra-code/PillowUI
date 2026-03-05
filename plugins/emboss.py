PLUGIN_NAME = "Emboss"
PLUGIN_DESCRIPTION = "Apply 3D embossed effect"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageFilter
    return image.filter(ImageFilter.EMBOSS)


def export_code(params):
    return "img = img.filter(ImageFilter.EMBOSS)"


def export_imports():
    return "from PIL import ImageFilter"

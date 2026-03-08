PLUGIN_NAME = "Sharpen (Filter)"
PLUGIN_DESCRIPTION = "Apply convolution-based sharpening (different from enhancement sharpness)"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageFilter
    return image.filter(ImageFilter.SHARPEN)


def export_code(params):
    return "img = img.filter(ImageFilter.SHARPEN)"


def export_imports():
    return "from PIL import ImageFilter"

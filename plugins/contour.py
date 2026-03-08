PLUGIN_NAME = "Contour"
PLUGIN_DESCRIPTION = "Trace contours to create a line-drawing effect"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageFilter
    return image.filter(ImageFilter.CONTOUR)


def export_code(params):
    return "img = img.filter(ImageFilter.CONTOUR)"


def export_imports():
    return "from PIL import ImageFilter"

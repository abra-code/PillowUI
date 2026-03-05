PLUGIN_NAME = "Gaussian Blur"
PLUGIN_DESCRIPTION = "Apply Gaussian blur"
PLUGIN_PARAMS = [
    {"name": "radius", "type": "float", "default": 2.0, "min": 0.1, "max": 50.0, "label": "Blur Radius"},
]


def transform(image, params):
    from PIL import ImageFilter
    radius = params.get("radius", 2.0)
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def export_code(params):
    radius = params.get("radius", 2.0)
    return f"img = img.filter(ImageFilter.GaussianBlur(radius={radius}))"


def export_imports():
    return "from PIL import ImageFilter"

PLUGIN_NAME = "Unsharp Mask"
PLUGIN_DESCRIPTION = "Professional sharpening with radius, strength, and threshold"
PLUGIN_PARAMS = [
    {"name": "radius", "type": "float", "default": 2.0, "min": 0.1, "max": 20.0, "label": "Radius"},
    {"name": "percent", "type": "float", "default": 150.0, "min": 0.0, "max": 500.0, "label": "Strength %", "step": 10.0},
    {"name": "threshold", "type": "float", "default": 3.0, "min": 0.0, "max": 20.0, "label": "Threshold", "step": 1.0},
]


def transform(image, params):
    from PIL import ImageFilter
    radius = params.get("radius", 2.0)
    percent = int(params.get("percent", 150.0))
    threshold = int(params.get("threshold", 3.0))
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))


def export_code(params):
    radius = params.get("radius", 2.0)
    percent = int(params.get("percent", 150.0))
    threshold = int(params.get("threshold", 3.0))
    return f"img = img.filter(ImageFilter.UnsharpMask(radius={radius}, percent={percent}, threshold={threshold}))"


def export_imports():
    return "from PIL import ImageFilter"

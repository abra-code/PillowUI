PLUGIN_NAME = "Median Filter"
PLUGIN_DESCRIPTION = "Reduce noise by replacing each pixel with the median of its neighbors"
PLUGIN_PARAMS = [
    {"name": "size", "type": "float", "default": 3.0, "min": 3.0, "max": 15.0, "step": 2.0, "label": "Window Size"},
]


def transform(image, params):
    from PIL import ImageFilter
    size = int(params.get("size", 3.0))
    # Must be odd
    if size % 2 == 0:
        size += 1
    return image.filter(ImageFilter.MedianFilter(size=size))


def export_code(params):
    size = int(params.get("size", 3.0))
    if size % 2 == 0:
        size += 1
    return f"img = img.filter(ImageFilter.MedianFilter(size={size}))"


def export_imports():
    return "from PIL import ImageFilter"

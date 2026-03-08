PLUGIN_NAME = "Border"
PLUGIN_DESCRIPTION = "Add a solid-color border around the image"
PLUGIN_PARAMS = [
    {"name": "size", "type": "float", "default": 10.0, "min": 1.0, "max": 200.0, "label": "Border Size"},
    {"name": "fill_r", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Color Red"},
    {"name": "fill_g", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Color Green"},
    {"name": "fill_b", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Color Blue"},
]


def transform(image, params):
    from PIL import ImageOps
    border = int(params.get("size", 10))
    fill = (
        int(params.get("fill_r", 0)),
        int(params.get("fill_g", 0)),
        int(params.get("fill_b", 0)),
    )
    if image.mode == "RGBA":
        fill = fill + (255,)
    return ImageOps.expand(image, border=border, fill=fill)


def export_code(params):
    border = int(params.get("size", 10))
    fill = (int(params.get("fill_r", 0)), int(params.get("fill_g", 0)), int(params.get("fill_b", 0)))
    return f"img = ImageOps.expand(img, border={border}, fill={fill})"


def export_imports():
    return "from PIL import ImageOps"

PLUGIN_NAME = "Solarize"
PLUGIN_DESCRIPTION = "Invert pixels above a brightness threshold"
PLUGIN_PARAMS = [
    {"name": "threshold", "type": "float", "default": 128.0, "min": 0.0, "max": 255.0, "label": "Threshold"},
]


def transform(image, params):
    from PIL import ImageOps
    threshold = int(params.get("threshold", 128.0))
    if image.mode == "RGBA":
        from PIL import Image
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.solarize(rgb, threshold)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    return ImageOps.solarize(image, threshold)


def export_code(params):
    threshold = int(params.get("threshold", 128.0))
    return f"img = ImageOps.solarize(img, {threshold})"


def export_imports():
    return "from PIL import ImageOps"

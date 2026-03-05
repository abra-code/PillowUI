PLUGIN_NAME = "Auto Contrast"
PLUGIN_DESCRIPTION = "Normalize image contrast automatically"
PLUGIN_PARAMS = [
    {"name": "cutoff", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0, "label": "Cutoff %", "step": 0.5},
]


def transform(image, params):
    from PIL import ImageOps
    cutoff = params.get("cutoff", 0.0)
    if image.mode == "RGBA":
        from PIL import Image
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.autocontrast(rgb, cutoff=cutoff)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    return ImageOps.autocontrast(image, cutoff=cutoff)


def export_code(params):
    cutoff = params.get("cutoff", 0.0)
    return f"img = ImageOps.autocontrast(img, cutoff={cutoff})"


def export_imports():
    return "from PIL import ImageOps"

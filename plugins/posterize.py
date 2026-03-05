PLUGIN_NAME = "Posterize"
PLUGIN_DESCRIPTION = "Reduce color depth by limiting bits per channel"
PLUGIN_PARAMS = [
    {"name": "bits", "type": "float", "default": 4.0, "min": 1.0, "max": 8.0, "label": "Bits per Channel", "step": 1.0},
]


def transform(image, params):
    from PIL import ImageOps
    bits = int(params.get("bits", 4.0))
    bits = max(1, min(8, bits))
    if image.mode == "RGBA":
        from PIL import Image
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.posterize(rgb, bits)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return ImageOps.posterize(image, bits)


def export_code(params):
    bits = int(params.get("bits", 4.0))
    return f"img = ImageOps.posterize(img, {bits})"


def export_imports():
    return "from PIL import ImageOps"

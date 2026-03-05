PLUGIN_NAME = "Invert"
PLUGIN_DESCRIPTION = "Negate all pixel values"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageOps
    # ImageOps.invert does not support RGBA; split off alpha if present
    if image.mode == "RGBA":
        r, g, b, a = image.split()
        from PIL import Image
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.invert(rgb)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return ImageOps.invert(image)


def export_code(params):
    return "img = ImageOps.invert(img.convert('RGB'))"


def export_imports():
    return "from PIL import ImageOps"

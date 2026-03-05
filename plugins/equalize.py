PLUGIN_NAME = "Equalize"
PLUGIN_DESCRIPTION = "Histogram equalization for uniform tonal distribution"
PLUGIN_PARAMS = []


def transform(image, params):
    from PIL import ImageOps
    if image.mode == "RGBA":
        from PIL import Image
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.equalize(rgb)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    return ImageOps.equalize(image)


def export_code(params):
    return "img = ImageOps.equalize(img)"


def export_imports():
    return "from PIL import ImageOps"

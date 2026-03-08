PLUGIN_NAME = "Self Blend"
PLUGIN_DESCRIPTION = "Blend the image with itself using Multiply or Screen"
PLUGIN_PARAMS = [
    {"name": "screen", "type": "bool", "default": False, "label": "Screen (lighten instead of darken)"},
    {"name": "intensity", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0, "label": "Intensity"},
]


def transform(image, params):
    from PIL import Image, ImageChops
    screen = params.get("screen", False)
    intensity = params.get("intensity", 0.5)
    if intensity == 0:
        return image

    alpha = None
    if image.mode == "RGBA":
        alpha = image.split()[-1]
        rgb = image.convert("RGB")
    else:
        rgb = image.convert("RGB") if image.mode != "RGB" else image

    if screen:
        blended = ImageChops.screen(rgb, rgb)
    else:
        blended = ImageChops.multiply(rgb, rgb)

    result = Image.blend(rgb, blended, intensity)
    if alpha is not None:
        result.putalpha(alpha)
    return result


def export_code(params):
    screen = params.get("screen", False)
    intensity = params.get("intensity", 0.5)
    op = "screen" if screen else "multiply"
    return (
        f"_alpha = img.split()[-1] if img.mode == 'RGBA' else None\n"
        f"_rgb = img.convert('RGB')\n"
        f"_blended = ImageChops.{op}(_rgb, _rgb)\n"
        f"img = Image.blend(_rgb, _blended, {intensity})\n"
        f"if _alpha is not None:\n"
        f"    img.putalpha(_alpha)"
    )


def export_imports():
    return "from PIL import Image, ImageChops"

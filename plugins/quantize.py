PLUGIN_NAME = "Quantize"
PLUGIN_DESCRIPTION = "Reduce to a limited number of colors (palette effect)"
PLUGIN_PARAMS = [
    {"name": "colors", "type": "float", "default": 16.0, "min": 2.0, "max": 256.0, "label": "Number of Colors"},
]


def transform(image, params):
    colors = int(params.get("colors", 16))
    colors = max(2, min(256, colors))
    original_mode = image.mode
    has_alpha = original_mode == "RGBA"
    if has_alpha:
        alpha = image.split()[-1]
        image = image.convert("RGB")
    elif original_mode != "RGB":
        image = image.convert("RGB")
    quantized = image.quantize(colors=colors, dither=1).convert("RGB")
    if has_alpha:
        quantized.putalpha(alpha)
    return quantized


def export_code(params):
    colors = int(params.get("colors", 16))
    colors = max(2, min(256, colors))
    return (
        f"_alpha = img.split()[-1] if img.mode == 'RGBA' else None\n"
        f"img = img.convert('RGB').quantize(colors={colors}, dither=1).convert('RGB')\n"
        f"if _alpha is not None:\n"
        f"    img.putalpha(_alpha)"
    )


def export_imports():
    return ""

PLUGIN_NAME = "Threshold"
PLUGIN_DESCRIPTION = "Convert to binary black & white using a brightness cutoff"
PLUGIN_PARAMS = [
    {"name": "threshold", "type": "float", "default": 128.0, "min": 0.0, "max": 255.0, "label": "Threshold"},
]


def transform(image, params):
    threshold = int(params.get("threshold", 128))
    alpha = None
    if image.mode == "RGBA":
        alpha = image.split()[-1]
    gray = image.convert("L")
    lut = [0 if i < threshold else 255 for i in range(256)]
    binary = gray.point(lut)
    result = binary.convert("RGB")
    if alpha is not None:
        result.putalpha(alpha)
    return result


def export_code(params):
    threshold = int(params.get("threshold", 128))
    return (
        f"_alpha = img.split()[-1] if img.mode == 'RGBA' else None\n"
        f"_lut = [0 if i < {threshold} else 255 for i in range(256)]\n"
        f"img = img.convert('L').point(_lut).convert('RGB')\n"
        f"if _alpha is not None:\n"
        f"    img.putalpha(_alpha)"
    )


def export_imports():
    return ""

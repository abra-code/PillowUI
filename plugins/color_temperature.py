PLUGIN_NAME = "Color Temperature"
PLUGIN_DESCRIPTION = "Shift color temperature: warm (positive) or cool (negative) via per-channel LUTs"
PLUGIN_PARAMS = [
    {"name": "temperature", "type": "float", "default": 0.0, "min": -100.0, "max": 100.0, "label": "Temperature"},
]


def transform(image, params):
    from PIL import Image
    temp = params.get("temperature", 0.0)
    if temp == 0:
        return image

    alpha = None
    if image.mode == "RGBA":
        r, g, b, alpha = image.split()
    else:
        img = image.convert("RGB") if image.mode != "RGB" else image
        r, g, b = img.split()

    # Warm = boost red, cut blue. Cool = opposite.
    shift = temp * 0.3
    r_lut = [max(0, min(255, int(i + shift))) for i in range(256)]
    b_lut = [max(0, min(255, int(i - shift))) for i in range(256)]
    r = r.point(r_lut)
    b = b.point(b_lut)

    if alpha is not None:
        return Image.merge("RGBA", (r, g, b, alpha))
    return Image.merge("RGB", (r, g, b))


def export_code(params):
    temp = params.get("temperature", 0.0)
    shift = temp * 0.3
    return (
        f"_alpha = img.split()[-1] if img.mode == 'RGBA' else None\n"
        f"_rgb = img.convert('RGB') if img.mode != 'RGB' else img\n"
        f"_r, _g, _b = _rgb.split()\n"
        f"_r_lut = [max(0, min(255, int(i + {shift:.1f}))) for i in range(256)]\n"
        f"_b_lut = [max(0, min(255, int(i - {shift:.1f}))) for i in range(256)]\n"
        f"_r = _r.point(_r_lut)\n"
        f"_b = _b.point(_b_lut)\n"
        f"if _alpha is not None:\n"
        f"    img = Image.merge('RGBA', (_r, _g, _b, _alpha))\n"
        f"else:\n"
        f"    img = Image.merge('RGB', (_r, _g, _b))"
    )


def export_imports():
    return "from PIL import Image"

PLUGIN_NAME = "Grayscale"
PLUGIN_DESCRIPTION = "Convert image to grayscale"
PLUGIN_PARAMS = []


def transform(image, params):
    original_mode = image.mode
    gray = image.convert("L")
    if original_mode == "RGBA":
        # Preserve alpha channel
        alpha = image.split()[-1]
        rgb = gray.convert("RGB")
        result = rgb.copy()
        result.putalpha(alpha)
        return result
    return gray.convert("RGB")


def export_code(params):
    return (
        "if img.mode == 'RGBA':\n"
        "    _alpha = img.split()[-1]\n"
        "    img = img.convert('L').convert('RGB')\n"
        "    img.putalpha(_alpha)\n"
        "else:\n"
        "    img = img.convert('L').convert('RGB')"
    )


def export_imports():
    return ""

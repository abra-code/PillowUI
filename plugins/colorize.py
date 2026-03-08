PLUGIN_NAME = "Colorize"
PLUGIN_DESCRIPTION = "Map grayscale values to a two-color gradient (tinting effect)"
PLUGIN_PARAMS = [
    {"name": "black_r", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Shadow Red"},
    {"name": "black_g", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Shadow Green"},
    {"name": "black_b", "type": "float", "default": 0.0, "min": 0.0, "max": 255.0, "label": "Shadow Blue"},
    {"name": "white_r", "type": "float", "default": 255.0, "min": 0.0, "max": 255.0, "label": "Highlight Red"},
    {"name": "white_g", "type": "float", "default": 255.0, "min": 0.0, "max": 255.0, "label": "Highlight Green"},
    {"name": "white_b", "type": "float", "default": 255.0, "min": 0.0, "max": 255.0, "label": "Highlight Blue"},
]


def transform(image, params):
    from PIL import ImageOps, Image
    black = (
        int(params.get("black_r", 0)),
        int(params.get("black_g", 0)),
        int(params.get("black_b", 0)),
    )
    white = (
        int(params.get("white_r", 255)),
        int(params.get("white_g", 255)),
        int(params.get("white_b", 255)),
    )
    alpha = None
    if image.mode == "RGBA":
        alpha = image.split()[-1]
    gray = image.convert("L")
    result = ImageOps.colorize(gray, black=black, white=white)
    if alpha is not None:
        result.putalpha(alpha)
    return result


def export_code(params):
    black = (int(params.get("black_r", 0)), int(params.get("black_g", 0)), int(params.get("black_b", 0)))
    white = (int(params.get("white_r", 255)), int(params.get("white_g", 255)), int(params.get("white_b", 255)))
    return (
        f"_alpha = img.split()[-1] if img.mode == 'RGBA' else None\n"
        f"img = ImageOps.colorize(img.convert('L'), black={black}, white={white})\n"
        f"if _alpha is not None:\n"
        f"    img.putalpha(_alpha)"
    )


def export_imports():
    return "from PIL import ImageOps"

PLUGIN_NAME = "Flip"
PLUGIN_DESCRIPTION = "Mirror image horizontally or vertically"
PLUGIN_PARAMS = [
    {"name": "horizontal", "type": "bool", "default": True, "label": "Horizontal (Mirror)"},
    {"name": "vertical", "type": "bool", "default": False, "label": "Vertical (Flip)"},
]


def transform(image, params):
    from PIL import ImageOps
    img = image
    if params.get("horizontal", True):
        img = ImageOps.mirror(img)
    if params.get("vertical", False):
        img = ImageOps.flip(img)
    return img


def export_code(params):
    lines = []
    if params.get("horizontal", True):
        lines.append("img = ImageOps.mirror(img)")
    if params.get("vertical", False):
        lines.append("img = ImageOps.flip(img)")
    return "\n".join(lines) if lines else "pass"


def export_imports():
    return "from PIL import ImageOps"

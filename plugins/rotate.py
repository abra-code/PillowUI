PLUGIN_NAME = "Rotate"
PLUGIN_DESCRIPTION = "Rotate image by angle"
PLUGIN_PARAMS = [
    {"name": "angle", "type": "float", "default": 0.0, "min": 0.0, "max": 360.0, "label": "Angle (degrees)"},
    {"name": "expand", "type": "bool", "default": False, "label": "Expand Canvas"},
]


def transform(image, params):
    angle = params.get("angle", 0.0)
    expand = params.get("expand", False)
    if image.mode == "RGBA":
        return image.rotate(angle, expand=expand, fillcolor=(0, 0, 0, 0))
    return image.rotate(angle, expand=expand, fillcolor=(0, 0, 0))


def export_code(params):
    angle = params.get("angle", 0.0)
    expand = params.get("expand", False)
    return (
        f"if img.mode == 'RGBA':\n"
        f"    img = img.rotate({angle}, expand={expand}, fillcolor=(0, 0, 0, 0))\n"
        f"else:\n"
        f"    img = img.rotate({angle}, expand={expand}, fillcolor=(0, 0, 0))"
    )


def export_imports():
    return ""

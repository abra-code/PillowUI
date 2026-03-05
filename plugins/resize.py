PLUGIN_NAME = "Resize"
PLUGIN_DESCRIPTION = "Resize image by percentage"
PLUGIN_PARAMS = [
    {"name": "percent", "type": "float", "default": 100.0, "min": 10.0, "max": 200.0, "label": "Scale (%)"},
]


def transform(image, params):
    percent = params.get("percent", 100.0)
    w, h = image.size
    new_w = max(1, int(w * percent / 100.0))
    new_h = max(1, int(h * percent / 100.0))
    return image.resize((new_w, new_h), resample=3)


def export_code(params):
    percent = params.get("percent", 100.0)
    return (
        f"w, h = img.size\n"
        f"img = img.resize((max(1, int(w * {percent} / 100.0)), max(1, int(h * {percent} / 100.0))), resample=3)"
    )


def export_imports():
    return ""

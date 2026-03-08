PLUGIN_NAME = "Text Watermark"
PLUGIN_DESCRIPTION = "Overlay text on the image"
PLUGIN_PARAMS = [
    {"name": "text", "type": "string", "default": "Sample", "label": "Text"},
    {"name": "font_size", "type": "float", "default": 48.0, "min": 8.0, "max": 200.0, "label": "Font Size"},
    {"name": "opacity", "type": "float", "default": 50.0, "min": 0.0, "max": 100.0, "label": "Opacity %"},
    {"name": "x_percent", "type": "float", "default": 95.0, "min": 0.0, "max": 100.0, "label": "X Position %"},
    {"name": "y_percent", "type": "float", "default": 95.0, "min": 0.0, "max": 100.0, "label": "Y Position %"},
]


def _get_font(size):
    from PIL import ImageFont
    for name in ("Helvetica", "Arial", "DejaVuSans"):
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size=size)


def transform(image, params):
    from PIL import Image, ImageDraw

    text = params.get("text", "Sample")
    if not text:
        return image

    font_size = int(params.get("font_size", 48))
    opacity = int(params.get("opacity", 50) * 255 / 100)
    x_pct = params.get("x_percent", 95.0)
    y_pct = params.get("y_percent", 95.0)

    font = _get_font(font_size)

    # Create transparent overlay
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Measure text and position it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = int((image.width - text_w) * x_pct / 100)
    y = int((image.height - text_h) * y_pct / 100)

    # Draw shadow for readability, then white text
    shadow = max(1, font_size // 24)
    draw.text((x + shadow, y + shadow), text, font=font, fill=(0, 0, 0, opacity))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

    # Composite
    was_rgb = image.mode != "RGBA"
    base = image.convert("RGBA") if was_rgb else image.copy()
    result = Image.alpha_composite(base, overlay)
    if was_rgb:
        result = result.convert(image.mode)
    return result


def export_code(params):
    text = params.get("text", "Sample")
    font_size = int(params.get("font_size", 48))
    opacity = int(params.get("opacity", 50) * 255 / 100)
    x_pct = params.get("x_percent", 95.0)
    y_pct = params.get("y_percent", 95.0)
    shadow = max(1, font_size // 24)
    return (
        f"_font = ImageFont.load_default(size={font_size})\n"
        f"_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))\n"
        f"_draw = ImageDraw.Draw(_overlay)\n"
        f"_bbox = _draw.textbbox((0, 0), {text!r}, font=_font)\n"
        f"_tw, _th = _bbox[2] - _bbox[0], _bbox[3] - _bbox[1]\n"
        f"_x = int((img.width - _tw) * {x_pct} / 100)\n"
        f"_y = int((img.height - _th) * {y_pct} / 100)\n"
        f"_draw.text((_x + {shadow}, _y + {shadow}), {text!r}, font=_font, fill=(0, 0, 0, {opacity}))\n"
        f"_draw.text((_x, _y), {text!r}, font=_font, fill=(255, 255, 255, {opacity}))\n"
        f"_was_rgb = img.mode != 'RGBA'\n"
        f"_base = img.convert('RGBA') if _was_rgb else img.copy()\n"
        f"img = Image.alpha_composite(_base, _overlay)\n"
        f"if _was_rgb:\n"
        f"    img = img.convert('RGB')"
    )


def export_imports():
    return "from PIL import Image, ImageDraw, ImageFont"

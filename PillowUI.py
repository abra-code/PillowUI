#!/usr/bin/env python3
"""PillowUI — Image Transformation Pipeline Builder"""

import json
import os
import sys
import importlib.util
import tempfile

import actionui
from PIL import Image

# Register optional format plugins if available
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- View ID Constants ---
PIPELINE_TABLE_ID = 10
BTN_REMOVE_ID = 21
BTN_MOVE_UP_ID = 22
BTN_MOVE_DOWN_ID = 23
BTN_EXPORT_ID = 24
BTN_IMPORT_ID = 25
PLUGIN_PICKER_ID = 30

PREVIEW_IMAGE_ID = 50

PARAM_GROUP_ID = 60
LOADABLE_PARAMS_ID = 200

BTN_OPEN_ID = 80
BTN_SAVE_ID = 81

OUTPUT_FORMAT_PICKER_ID = 90
OUTPUT_QUALITY_LABEL_ID = 91
OUTPUT_QUALITY_SLIDER_ID = 92
OUTPUT_QUALITY_TEXT_ID = 93
OUTPUT_QUALITY_ROW_ID = 95

# --- Application State ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(SCRIPT_DIR, "plugins")
ICON_PATH = os.path.join(SCRIPT_DIR, "Pillow.png")

app = actionui.Application(name="PillowUI", icon=ICON_PATH)

# Plugin registry: list of loaded plugin modules (shared across all windows)
plugin_registry = []  # [module, ...]
plugin_names = []     # [name, ...]
plugin_json_paths = {}  # {module: absolute_path_to_params_json}

# Output format support (populated at launch by _build_format_list)
_QUALITY_FORMATS = {"JPEG", "WEBP", "AVIF", "HEIF"}
_saveable_formats = []   # [(display_name, pillow_format, extension), ...]
_format_to_ext = {}      # pillow_format -> ".ext"


# --- Per-Window State ---

class WindowState:
    """Holds all state for a single PillowUI window."""
    def __init__(self, window):
        self.window = window
        self.pipeline = []  # [{"plugin": module, "params": {}, "enabled": True}, ...]
        self.source_image = None
        self.processed_image = None
        self.selected_pipeline_idx = -1
        self.preview_temp_path = None
        self.output_format = "original"
        self.output_quality = 85

    def cleanup(self):
        if self.preview_temp_path and os.path.exists(self.preview_temp_path):
            try:
                os.unlink(self.preview_temp_path)
            except OSError:
                pass


_window_states = {}  # window_uuid -> WindowState


def _get_state(ctx):
    """Look up WindowState for an action context."""
    return _window_states.get(ctx.window_uuid)


# --- Plugin Loader ---

def load_plugins():
    """Scan plugins/ directory and import all plugin modules."""
    global plugin_registry, plugin_names
    plugin_registry = []
    plugin_names = []
    if not os.path.isdir(PLUGINS_DIR):
        return
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(PLUGINS_DIR, fname)
        mod_name = fname[:-3]
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            if hasattr(mod, "PLUGIN_NAME") and hasattr(mod, "transform"):
                plugin_registry.append(mod)
        except Exception as e:
            print(f"Failed to load plugin {fname}: {e}", file=sys.stderr)
    # Sort by display name so the picker menu is alphabetical
    plugin_registry.sort(key=lambda m: m.PLUGIN_NAME)
    plugin_names = [m.PLUGIN_NAME for m in plugin_registry]


def get_default_params(plugin_mod):
    """Return a dict of default param values for a plugin."""
    params = {}
    for p in getattr(plugin_mod, "PLUGIN_PARAMS", []):
        params[p["name"]] = p["default"]
    return params


def _build_format_list():
    """Build the list of saveable image formats from Pillow at launch."""
    global _saveable_formats, _format_to_ext
    _DISPLAY_NAMES = {
        "BMP": "BMP", "DIB": "DIB", "EPS": "EPS", "GIF": "GIF",
        "ICNS": "ICNS", "ICO": "ICO", "JPEG": "JPEG",
        "JPEG2000": "JPEG 2000", "MSP": "MSP", "PCX": "PCX",
        "PDF": "PDF", "PNG": "PNG", "PPM": "PPM", "SGI": "SGI",
        "TGA": "TGA", "TIFF": "TIFF", "WEBP": "WebP", "XBM": "XBM",
        "HEIF": "HEIF/HEIC",
    }
    _PREFERRED_EXT = {"JPEG": ".jpg", "TIFF": ".tiff", "JPEG2000": ".jp2"}

    # Map each Pillow format to its shortest registered extension
    ext_map = {}
    for ext, fmt in Image.registered_extensions().items():
        if fmt in Image.SAVE:
            prev = ext_map.get(fmt)
            if prev is None or len(ext) < len(prev):
                ext_map[fmt] = ext
    for fmt, ext in _PREFERRED_EXT.items():
        if fmt in ext_map:
            ext_map[fmt] = ext
    _format_to_ext = dict(ext_map)

    formats = []
    for fmt in sorted(ext_map):
        display = _DISPLAY_NAMES.get(fmt, fmt)
        formats.append((display, fmt, ext_map[fmt]))
    _saveable_formats = formats


def _has_alpha(img):
    """Check whether a PIL Image has an alpha channel."""
    return img.mode in ("RGBA", "LA", "PA", "RGBa", "La") or (
        img.mode == "P" and "transparency" in img.info
    )


def _update_quality_visibility(state):
    """Show or hide the quality controls based on the selected output format."""
    fmt = state.output_format
    if fmt == "original":
        show = bool(state.source_image and state.source_image.format in _QUALITY_FORMATS)
    else:
        show = fmt in _QUALITY_FORMATS
    state.window.set_property(OUTPUT_QUALITY_ROW_ID, "hidden", not show)


def _sync_output_controls(state):
    """Push current output_format and output_quality from state into the UI."""
    state.window.set_string(OUTPUT_FORMAT_PICKER_ID, state.output_format)
    state.window.set_double(OUTPUT_QUALITY_SLIDER_ID, float(state.output_quality))
    state.window.set_string(OUTPUT_QUALITY_TEXT_ID, str(state.output_quality))
    _update_quality_visibility(state)


def _resolve_output(state):
    """Determine Pillow format, extension, and save kwargs for current settings."""
    fmt = state.output_format
    img = state.processed_image

    if fmt == "original":
        src_fmt = state.source_image.format if state.source_image else None
        if src_fmt and src_fmt in Image.SAVE:
            fmt = src_fmt
        elif img and _has_alpha(img):
            fmt = "PNG"
        else:
            fmt = "JPEG"

    ext = _format_to_ext.get(fmt, ".png")
    kwargs = {"format": fmt}
    if fmt in _QUALITY_FORMATS:
        kwargs["quality"] = state.output_quality

    return fmt, ext, kwargs


def generate_plugin_params_json(plugin_mod):
    """Generate an ActionUI JSON dict for a plugin's PLUGIN_PARAMS."""
    params_def = getattr(plugin_mod, "PLUGIN_PARAMS", [])
    description = getattr(plugin_mod, "PLUGIN_DESCRIPTION", "")
    # Invisible divider forces VStack to expand to full parent width.
    # Placed last with zero padding so it doesn't shift visible content.
    width_filler = {"type": "Divider", "properties": {"opacity": 0, "frame": {"height": 0}, "padding": 0}}

    desc_text = {
        "type": "Text",
        "properties": {
            "text": description or "No parameters to configure",
            "foregroundStyle": "secondary",
        },
    }

    if not params_def:
        return {
            "type": "VStack",
            "id": 1000,
            "properties": {
                "spacing": 8.0,
                "padding": "default",
                "alignment": "leading",
            },
            "children": [desc_text, width_filler],
        }

    children = [desc_text]
    control_id = 1001
    for pdef in params_def:
        if pdef["type"] == "float":
            slider_props = {
                "value": pdef["default"],
                "range": {"min": pdef.get("min", 0.0), "max": pdef.get("max", 1.0)},
                "valueChangeActionID": f"param.{pdef['name']}.changed",
            }
            if "step" in pdef:
                slider_props["step"] = pdef["step"]
            text_field_id = control_id + 1000
            children.append({
                "type": "HStack",
                "properties": {},
                "children": [
                    {
                        "type": "Text",
                        "properties": {
                            "text": pdef.get("label", pdef["name"]),
                            "frame": {"width": 140},
                        },
                    },
                    {
                        "type": "Slider",
                        "id": control_id,
                        "properties": slider_props,
                    },
                    {
                        "type": "TextField",
                        "id": text_field_id,
                        "properties": {
                            "text": _format_param_value(pdef["default"], pdef),
                            "placeholder": "",
                            "frame": {"width": 60},
                            "valueChangeActionID": f"param.{pdef['name']}.text.changed",
                        },
                    },
                ],
            })
            control_id += 1
        elif pdef["type"] == "bool":
            children.append({
                "type": "Toggle",
                "id": control_id,
                "properties": {
                    "title": pdef.get("label", pdef["name"]),
                    "valueChangeActionID": f"param.{pdef['name']}.changed",
                },
            })
            control_id += 1
        elif pdef["type"] == "string":
            children.append({
                "type": "HStack",
                "properties": {},
                "children": [
                    {
                        "type": "Text",
                        "properties": {
                            "text": pdef.get("label", pdef["name"]),
                            "frame": {"width": 140},
                        },
                    },
                    {
                        "type": "TextField",
                        "id": control_id,
                        "properties": {
                            "text": str(pdef.get("default", "")),
                            "placeholder": pdef.get("placeholder", ""),
                            "valueChangeActionID": f"param.{pdef['name']}.text.changed",
                        },
                    },
                ],
            })
            control_id += 1

    return {
        "type": "VStack",
        "id": 1000,
        "properties": {
            "spacing": 10.0,
            "padding": "default",
            "alignment": "leading",
        },
        "children": children + [width_filler],
    }


def generate_all_plugin_json():
    """Generate per-plugin params JSON files and populate plugin_json_paths."""
    global plugin_json_paths
    plugin_json_paths = {}
    for mod in plugin_registry:
        json_dict = generate_plugin_params_json(mod)
        mod_name = mod.__name__
        json_path = os.path.join(PLUGINS_DIR, f"{mod_name}_params.json")
        with open(json_path, "w") as f:
            json.dump(json_dict, f, indent=2)
        plugin_json_paths[mod] = json_path


# --- Pipeline Execution ---

def execute_pipeline(state):
    """Run all enabled pipeline steps on the source image."""
    if state.source_image is None:
        state.processed_image = None
        return
    img = state.source_image.copy()
    for step in state.pipeline:
        if not step["enabled"]:
            continue
        try:
            img = step["plugin"].transform(img, step["params"])
        except Exception as e:
            print(f"Plugin error ({step['plugin'].PLUGIN_NAME}): {e}", file=sys.stderr)
    state.processed_image = img


def update_preview(state):
    """Save processed image to temp file and update the Image view."""
    if state.processed_image is None:
        state.window.set_string(PREVIEW_IMAGE_ID, "photo")
        return
    if state.preview_temp_path is None:
        fd, state.preview_temp_path = tempfile.mkstemp(suffix=".png", prefix="pillowui_")
        os.close(fd)
    state.processed_image.save(state.preview_temp_path, "PNG")
    state.window.set_string(PREVIEW_IMAGE_ID, state.preview_temp_path)


def refresh_pipeline(state):
    """Re-execute pipeline and update preview."""
    execute_pipeline(state)
    update_preview(state)


# --- Table Sync ---

def sync_table(state):
    """Sync the pipeline table rows with the pipeline state."""
    rows = []
    for i, step in enumerate(state.pipeline):
        rows.append([
            str(i + 1),
            step["plugin"].PLUGIN_NAME,
        ])
    state.window.set_rows(PIPELINE_TABLE_ID, rows)


def update_toolbar_buttons(state):
    """Enable/disable toolbar buttons based on selection state."""
    has_selection = 0 <= state.selected_pipeline_idx < len(state.pipeline)
    state.window.set_property(BTN_REMOVE_ID, "disabled", not has_selection)
    state.window.set_property(BTN_MOVE_UP_ID, "disabled", not has_selection or state.selected_pipeline_idx <= 0)
    state.window.set_property(BTN_MOVE_DOWN_ID, "disabled", not has_selection or state.selected_pipeline_idx >= len(state.pipeline) - 1)


# --- Parameter UI ---

def show_params_for_step(state, step_idx):
    """Update the parameter panel to show controls for the selected pipeline step."""
    if step_idx < 0 or step_idx >= len(state.pipeline):
        state.window.set_property(PARAM_GROUP_ID, "title", "Parameters")
        state.window.set_string(LOADABLE_PARAMS_ID, os.path.join(PLUGINS_DIR, "empty_params.json"))
        state._current_params_plugin = None
        return

    step = state.pipeline[step_idx]
    plugin_mod = step["plugin"]
    state.window.set_property(PARAM_GROUP_ID, "title", f"{plugin_mod.PLUGIN_NAME} Parameters")

    json_path = plugin_json_paths.get(plugin_mod, "")

    # Only reload the LoadableView if the plugin actually changed.
    # Re-setting the same path triggers an async reload that destroys
    # controls before _sync_param_values can update them.
    if getattr(state, '_current_params_plugin', None) is not plugin_mod:
        state.window.set_string(LOADABLE_PARAMS_ID, json_path)
        state._current_params_plugin = plugin_mod
    else:
        # Same plugin already loaded – just sync the values directly.
        _sync_param_values(state, step_idx)


def _format_param_value(value, pdef):
    """Format a float param value for display in the text field."""
    step_val = pdef.get("step")
    if step_val is not None and step_val == int(step_val):
        return str(int(value))
    if abs(value) >= 100:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _sync_param_values(state, step_idx):
    """Set current param values on the dynamically loaded controls."""
    if step_idx < 0 or step_idx >= len(state.pipeline):
        return
    step = state.pipeline[step_idx]
    params_def = getattr(step["plugin"], "PLUGIN_PARAMS", [])
    control_id = 1001
    for pdef in params_def:
        value = step["params"].get(pdef["name"], pdef["default"])
        if pdef["type"] == "float":
            state.window.set_double(control_id, value)
            state.window.set_string(control_id + 1000, _format_param_value(value, pdef))
        elif pdef["type"] == "bool":
            state.window.set_bool(control_id, value)
        elif pdef["type"] == "string":
            state.window.set_string(control_id, str(value))
        control_id += 1


# --- Export / Import ---

def export_pipeline_script(state):
    """Generate a standalone Python script from the current pipeline."""
    import inspect
    import textwrap

    # Collect pipeline data and unique transform functions
    steps = []
    transforms = {}  # plugin_name -> source code of transform()
    for step in state.pipeline:
        if not step["enabled"]:
            continue
        plugin = step["plugin"]
        name = plugin.PLUGIN_NAME
        steps.append({"plugin": name, "params": dict(step["params"])})
        if name not in transforms:
            transforms[name] = textwrap.dedent(inspect.getsource(plugin.transform))

    # Build PIPELINE literal
    pipeline_repr = json.dumps(steps, indent=2)

    # Build transform functions, each renamed to _transform_<sanitized_name>
    func_defs = []
    for name, src in transforms.items():
        safe = name.lower().replace(" ", "_")
        renamed = src.replace("def transform(", f"def _transform_{safe}(", 1)
        func_defs.append(renamed)

    # Build dispatch dict
    dispatch_entries = []
    for name in transforms:
        safe = name.lower().replace(" ", "_")
        dispatch_entries.append(f'    "{name}": _transform_{safe},')
    dispatch = "{\n" + "\n".join(dispatch_entries) + "\n}"

    func_block = "\n\n".join(func_defs)

    # Build format extension map for the exported script
    fmt_ext_repr = json.dumps(_format_to_ext)

    script = f'''#!/usr/bin/env python3
"""Generated by PillowUI"""

import os
import sys
from PIL import Image

# --- Pipeline definition ---
# Each step: {{"plugin": "<name>", "params": {{...}}}}
PIPELINE = {pipeline_repr}

# --- Output settings ---
OUTPUT_FORMAT = "{state.output_format}"
OUTPUT_QUALITY = {state.output_quality}

# --- Transform functions (embedded from plugins) ---

{func_block}

_TRANSFORMS = {dispatch}

# --- Image format support ---

_IMAGE_EXTENSIONS = set()
for _ext, _fmt in Image.registered_extensions().items():
    if _fmt in Image.OPEN:
        _IMAGE_EXTENSIONS.add(_ext.lower())

_SAVEABLE_FORMATS = set(Image.SAVE.keys())
_QUALITY_FORMATS = {{"JPEG", "WEBP", "AVIF", "HEIF"}}
_FORMAT_EXTENSIONS = {fmt_ext_repr}


def _has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA", "RGBa", "La") or (
        img.mode == "P" and "transparency" in img.info
    )


def _resolve_format(img):
    """Determine the output Pillow format based on OUTPUT_FORMAT setting."""
    fmt = OUTPUT_FORMAT
    if fmt == "original":
        if img.format in _SAVEABLE_FORMATS:
            return img.format
        elif _has_alpha(img):
            return "PNG"
        else:
            return "JPEG"
    return fmt


def process(input_path, output_path):
    img = Image.open(input_path)
    fmt = _resolve_format(img)
    ext = _FORMAT_EXTENSIONS.get(fmt, ".png")
    stem = os.path.splitext(output_path)[0]
    output_path = stem + ext
    for step in PIPELINE:
        transform = _TRANSFORMS[step["plugin"]]
        img = transform(img, step["params"])
    save_kwargs = {{"format": fmt}}
    if fmt in _QUALITY_FORMATS:
        save_kwargs["quality"] = OUTPUT_QUALITY
    if fmt == "JPEG" and img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(output_path, **save_kwargs)
    print(f"Saved to {{output_path}}")


def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for name in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(name)[1].lower()
        if ext not in _IMAGE_EXTENSIONS:
            continue
        process(
            os.path.join(input_dir, name),
            os.path.join(output_dir, name),
        )
        count += 1
    print(f"Processed {{count}} image(s)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pillow_pipeline.py <input> <output>")
        print("  input/output can be files or directories")
        sys.exit(1)

    src, dst = sys.argv[1], sys.argv[2]
    if os.path.isdir(src):
        process_directory(src, dst)
    else:
        process(src, dst)
'''

    return script


def import_pipeline_into(state, path):
    """Import a previously exported pipeline script into a window state."""
    spec = importlib.util.spec_from_file_location("_imported_pipeline", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    imported = getattr(mod, "PIPELINE", None)
    if not imported:
        print("No PIPELINE found in script", file=sys.stderr)
        return False

    # Build name -> plugin module lookup
    name_to_plugin = {m.PLUGIN_NAME: m for m in plugin_registry}

    new_pipeline = []
    for step_data in imported:
        name = step_data["plugin"]
        params = step_data.get("params", {})
        plugin_mod = name_to_plugin.get(name)
        if plugin_mod is None:
            print(f"Plugin '{name}' not found, skipping", file=sys.stderr)
            continue
        # Merge imported params over defaults (handles new params added later)
        merged = get_default_params(plugin_mod)
        merged.update(params)
        new_pipeline.append({
            "plugin": plugin_mod,
            "params": merged,
            "enabled": True,
        })

    state.pipeline = new_pipeline

    # Restore output format settings if present
    imported_fmt = getattr(mod, "OUTPUT_FORMAT", None)
    if imported_fmt:
        state.output_format = imported_fmt
    imported_quality = getattr(mod, "OUTPUT_QUALITY", None)
    if imported_quality is not None:
        state.output_quality = int(imported_quality)

    return True


# --- Window Creation ---

def _init_window(window):
    """Set up a newly created window with plugin picker and empty params."""
    state = WindowState(window)
    _window_states[window.uuid] = state

    window.set_string(LOADABLE_PARAMS_ID, os.path.join(PLUGINS_DIR, "empty_params.json"))

    if plugin_names:
        options = [{"title": name, "tag": str(i + 1)} for i, name in enumerate(plugin_names)]
        window.set_property(PLUGIN_PICKER_ID, "options", options)
        window.set_string(PLUGIN_PICKER_ID, "1")

    # Populate output format picker
    fmt_options = [{"title": "Original", "tag": "original"}]
    for display, fmt, ext in _saveable_formats:
        fmt_options.append({"title": display, "tag": fmt})
    window.set_property(OUTPUT_FORMAT_PICKER_ID, "options", fmt_options)
    window.set_string(OUTPUT_FORMAT_PICKER_ID, "original")

    return state


def create_window(title="PillowUI", pipeline_path=None, image_path=None):
    """Create a new PillowUI window, optionally with a pipeline and/or image."""
    json_path = os.path.join(SCRIPT_DIR, "PillowUI.json")
    window = app.load_and_present_window(json_path, title=title)
    # _init_window is called from window_will_present before we get here,
    # so state already exists
    state = _window_states.get(window.uuid)
    if state is None:
        state = _init_window(window)

    if pipeline_path:
        path = os.path.abspath(pipeline_path)
        if os.path.isfile(path):
            if import_pipeline_into(state, path):
                state.selected_pipeline_idx = 0 if state.pipeline else -1
                sync_table(state)
                show_params_for_step(state, state.selected_pipeline_idx)
                update_toolbar_buttons(state)
                _sync_output_controls(state)
        else:
            print(f"Pipeline not found: {path}", file=sys.stderr)

    if image_path:
        path = os.path.abspath(image_path)
        if os.path.isfile(path):
            try:
                state.source_image = Image.open(path)
                state.window.set_property(BTN_SAVE_ID, "disabled", False)
                refresh_pipeline(state)
                _update_quality_visibility(state)
            except Exception as e:
                print(f"Failed to open image: {e}", file=sys.stderr)
        else:
            print(f"Image not found: {path}", file=sys.stderr)

    return state


# --- Action Handlers ---

@app.action("image.open")
def on_image_open(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    paths = app.open_panel(
        title="Open Image",
        prompt="Open",
        allowed_types=["public.image"],
    )
    if not paths:
        return
    try:
        state.source_image = Image.open(paths[0])
    except Exception as e:
        print(f"Failed to open image: {e}", file=sys.stderr)
        return
    state.window.set_property(BTN_SAVE_ID, "disabled", False)
    refresh_pipeline(state)
    _update_quality_visibility(state)


@app.action("image.save")
def on_image_save(ctx):
    state = _get_state(ctx)
    if state is None or state.processed_image is None:
        return
    fmt, ext, save_kwargs = _resolve_output(state)
    path = app.save_panel(
        title="Save Image",
        prompt="Save",
        filename=f"output{ext}",
        allowed_types=[ext.lstrip(".")],
    )
    if not path:
        return
    try:
        img = state.processed_image
        if fmt == "JPEG" and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(path, **save_kwargs)
    except Exception as e:
        print(f"Failed to save image: {e}", file=sys.stderr)


@app.action("output.format.changed")
def on_output_format_changed(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    tag = state.window.get_string(OUTPUT_FORMAT_PICKER_ID)
    if tag:
        state.output_format = tag
    _update_quality_visibility(state)


@app.action("output.quality.changed")
def on_output_quality_changed(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    value = state.window.get_double(OUTPUT_QUALITY_SLIDER_ID)
    if value is not None:
        quality = max(1, min(100, int(value)))
        state.output_quality = quality
        state.window.set_string(OUTPUT_QUALITY_TEXT_ID, str(quality))


@app.action("output.quality.text.changed")
def on_output_quality_text_changed(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    text = state.window.get_string(OUTPUT_QUALITY_TEXT_ID)
    if text:
        try:
            quality = max(1, min(100, int(text)))
            state.output_quality = quality
            state.window.set_double(OUTPUT_QUALITY_SLIDER_ID, float(quality))
        except ValueError:
            pass


@app.action("pipeline.add")
def on_pipeline_add(ctx):
    state = _get_state(ctx)
    if state is None or not plugin_registry:
        return
    # Get selected plugin from picker
    tag = state.window.get_string(PLUGIN_PICKER_ID)
    idx = 0
    if tag is not None:
        try:
            idx = int(tag) - 1
        except (ValueError, TypeError):
            idx = 0
    if idx < 0 or idx >= len(plugin_registry):
        idx = 0

    plugin_mod = plugin_registry[idx]
    step = {
        "plugin": plugin_mod,
        "params": get_default_params(plugin_mod),
        "enabled": True,
    }
    state.pipeline.append(step)
    sync_table(state)
    update_toolbar_buttons(state)
    refresh_pipeline(state)


@app.action("pipeline.remove")
def on_pipeline_remove(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    if state.selected_pipeline_idx < 0 or state.selected_pipeline_idx >= len(state.pipeline):
        return
    state.pipeline.pop(state.selected_pipeline_idx)
    if state.selected_pipeline_idx >= len(state.pipeline):
        state.selected_pipeline_idx = len(state.pipeline) - 1
    sync_table(state)
    show_params_for_step(state, state.selected_pipeline_idx)
    update_toolbar_buttons(state)
    refresh_pipeline(state)


@app.action("pipeline.move.up")
def on_pipeline_move_up(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    idx = state.selected_pipeline_idx
    if idx <= 0 or idx >= len(state.pipeline):
        return
    state.pipeline[idx], state.pipeline[idx - 1] = state.pipeline[idx - 1], state.pipeline[idx]
    state.selected_pipeline_idx = idx - 1
    sync_table(state)
    update_toolbar_buttons(state)
    refresh_pipeline(state)


@app.action("pipeline.move.down")
def on_pipeline_move_down(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    idx = state.selected_pipeline_idx
    if idx < 0 or idx >= len(state.pipeline) - 1:
        return
    state.pipeline[idx], state.pipeline[idx + 1] = state.pipeline[idx + 1], state.pipeline[idx]
    state.selected_pipeline_idx = idx + 1
    sync_table(state)
    update_toolbar_buttons(state)
    refresh_pipeline(state)


@app.action("pipeline.selection.changed")
def on_pipeline_selection_changed(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    selected_row = state.window.get_value(PIPELINE_TABLE_ID)
    if selected_row is None or len(selected_row) == 0:
        state.selected_pipeline_idx = -1
    else:
        # First column is the row number
        try:
            state.selected_pipeline_idx = int(selected_row[0]) - 1
        except (ValueError, TypeError, IndexError):
            state.selected_pipeline_idx = -1
    show_params_for_step(state, state.selected_pipeline_idx)
    update_toolbar_buttons(state)


@app.action("pipeline.export")
def on_pipeline_export(ctx):
    state = _get_state(ctx)
    if state is None or not state.pipeline:
        return
    script = export_pipeline_script(state)
    path = app.save_panel(
        title="Export Pipeline Script",
        prompt="Export",
        filename="pillow_pipeline.py",
        allowed_types=["py"],
    )
    if not path:
        return
    try:
        with open(path, "w") as f:
            f.write(script)
        os.chmod(path, 0o755)
    except Exception as e:
        print(f"Failed to export: {e}", file=sys.stderr)


@app.action("pipeline.import")
def on_pipeline_import(ctx):
    state = _get_state(ctx)
    if state is None:
        return
    if state.pipeline:
        result = app.alert(
            title="Replace Pipeline?",
            message="The current pipeline will be replaced by the imported one.",
            style="warning",
            buttons=["Replace", "Cancel"],
        )
        if result != "Replace":
            return
    paths = app.open_panel(
        title="Import Pipeline Script",
        prompt="Import",
        allowed_types=["py"],
    )
    if not paths:
        return
    try:
        if import_pipeline_into(state, paths[0]):
            state.selected_pipeline_idx = 0 if state.pipeline else -1
            sync_table(state)
            show_params_for_step(state, state.selected_pipeline_idx)
            update_toolbar_buttons(state)
            _sync_output_controls(state)
            refresh_pipeline(state)
    except Exception as e:
        print(f"Failed to import: {e}", file=sys.stderr)


@app.action("plugin.picker.changed")
def on_plugin_picker_changed(ctx):
    # Just updates the picker selection state; add happens via "+" button
    pass


@app.action("params.view.loaded")
def on_params_view_loaded(ctx):
    """Called by LoadableView after the plugin params UI has loaded.
    Syncs the pipeline step's current param values into the controls."""
    state = _get_state(ctx)
    if state is None:
        return
    _sync_param_values(state, state.selected_pipeline_idx)


# Default action handler for dynamically loaded param controls
def on_dynamic_param_changed(ctx):
    action = ctx.action_id
    if not action.startswith("param."):
        return

    state = _get_state(ctx)
    if state is None:
        return

    # Determine if this is a text field change or a slider/toggle change
    is_text = action.endswith(".text.changed")
    if is_text:
        param_name = action[len("param."):-len(".text.changed")]
    elif action.endswith(".changed"):
        param_name = action[len("param."):-len(".changed")]
    else:
        return

    if state.selected_pipeline_idx < 0 or state.selected_pipeline_idx >= len(state.pipeline):
        return
    step = state.pipeline[state.selected_pipeline_idx]
    params_def = getattr(step["plugin"], "PLUGIN_PARAMS", [])

    # Find the control_id for this param to compute slider/text field IDs
    control_id = 1001
    for pdef in params_def:
        if pdef["name"] == param_name:
            if pdef["type"] == "float":
                slider_id = control_id
                text_field_id = control_id + 1000
                if is_text:
                    # Text field changed — parse value, update slider and param
                    text_val = state.window.get_string(text_field_id)
                    if text_val is not None:
                        try:
                            value = float(text_val)
                            pmin = pdef.get("min", 0.0)
                            pmax = pdef.get("max", 1.0)
                            value = max(pmin, min(pmax, value))
                            step["params"][param_name] = value
                            state.window.set_double(slider_id, value)
                        except ValueError:
                            pass
                else:
                    # Slider changed — update text field and param
                    value = state.window.get_double(slider_id)
                    if value is not None:
                        step["params"][param_name] = value
                        state.window.set_string(text_field_id, _format_param_value(value, pdef))
            elif pdef["type"] == "bool" and not is_text:
                value = state.window.get_bool(ctx.view_id)
                if value is not None:
                    step["params"][param_name] = value
            elif pdef["type"] == "string" and is_text:
                text_val = state.window.get_string(control_id)
                if text_val is not None:
                    step["params"][param_name] = text_val
            refresh_pipeline(state)
            return
        control_id += 1


# --- Menu Action Handlers ---

@app.action("file.new")
def on_file_new(ctx):
    create_window()


@app.action("file.open_image")
def on_file_open_image(ctx):
    paths = app.open_panel(
        title="Open Image",
        prompt="Open",
        allowed_types=["public.image"],
    )
    if not paths:
        return
    state = _get_state(ctx)
    if state is not None:
        # Open in the front window
        try:
            state.source_image = Image.open(paths[0])
        except Exception as e:
            print(f"Failed to open image: {e}", file=sys.stderr)
            return
        state.window.set_property(BTN_SAVE_ID, "disabled", False)
        refresh_pipeline(state)
        _update_quality_visibility(state)
    else:
        create_window(image_path=paths[0])


@app.action("file.import_pipeline")
def on_file_import_pipeline(ctx):
    state = _get_state(ctx)
    if state is not None and state.pipeline:
        result = app.alert(
            title="Replace Pipeline?",
            message="The current pipeline will be replaced by the imported one.",
            style="warning",
            buttons=["Replace", "Cancel"],
        )
        if result != "Replace":
            return
    paths = app.open_panel(
        title="Import Pipeline Script",
        prompt="Import",
        allowed_types=["py"],
    )
    if not paths:
        return
    if state is not None:
        try:
            if import_pipeline_into(state, paths[0]):
                state.selected_pipeline_idx = 0 if state.pipeline else -1
                sync_table(state)
                show_params_for_step(state, state.selected_pipeline_idx)
                update_toolbar_buttons(state)
                _sync_output_controls(state)
                refresh_pipeline(state)
        except Exception as e:
            print(f"Failed to import: {e}", file=sys.stderr)
    else:
        create_window(pipeline_path=paths[0])


@app.action("file.save_image")
def on_file_save_image(ctx):
    state = _get_state(ctx)
    if state is None or state.processed_image is None:
        return
    fmt, ext, save_kwargs = _resolve_output(state)
    path = app.save_panel(
        title="Save Image",
        prompt="Save",
        filename=f"output{ext}",
        allowed_types=[ext.lstrip(".")],
    )
    if not path:
        return
    try:
        img = state.processed_image
        if fmt == "JPEG" and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(path, **save_kwargs)
    except Exception as e:
        print(f"Failed to save image: {e}", file=sys.stderr)


@app.action("file.export_pipeline")
def on_file_export_pipeline(ctx):
    state = _get_state(ctx)
    if state is None or not state.pipeline:
        return
    script = export_pipeline_script(state)
    path = app.save_panel(
        title="Export Pipeline Script",
        prompt="Export",
        filename="pillow_pipeline.py",
        allowed_types=["py"],
    )
    if not path:
        return
    try:
        with open(path, "w") as f:
            f.write(script)
        os.chmod(path, 0o755)
    except Exception as e:
        print(f"Failed to export: {e}", file=sys.stderr)


# --- Lifecycle ---

@app.window_will_present
def on_window_present(window):
    if window.uuid not in _window_states:
        _init_window(window)


@app.window_will_close
def on_window_close(window):
    state = _window_states.pop(window.uuid, None)
    if state:
        state.cleanup()


@app.did_finish_launching
def on_launch():
    load_plugins()
    generate_all_plugin_json()
    _build_format_list()
    app.set_default_handler(on_dynamic_param_changed)

    app.load_menu_bar(json.dumps([
        {
            "type": "CommandGroup",
            "properties": {
                "placement": "replacing",
                "placementTarget": "newItem",
            },
            "children": [
                {
                    "type": "Button",
                    "properties": {
                        "title": "New",
                        "actionID": "file.new",
                        "keyboardShortcut": {"key": "n", "modifiers": ["command"]},
                    },
                },
                {
                    "type": "Button",
                    "properties": {
                        "title": "Open Image...",
                        "actionID": "file.open_image",
                        "keyboardShortcut": {"key": "o", "modifiers": ["command"]},
                    },
                },
                {
                    "type": "Button",
                    "properties": {
                        "title": "Import Pipeline...",
                        "actionID": "file.import_pipeline",
                        "keyboardShortcut": {"key": "i", "modifiers": ["command"]},
                    },
                },
                {"type": "Divider"},
            ],
        },
        {
            "type": "CommandGroup",
            "properties": {
                "placement": "after",
                "placementTarget": "saveItem",
            },
            "children": [
                {
                    "type": "Button",
                    "properties": {
                        "title": "Save Image...",
                        "actionID": "file.save_image",
                        "keyboardShortcut": {"key": "s", "modifiers": ["command"]},
                    },
                },
            ],
        },
        {
            "type": "CommandGroup",
            "properties": {
                "placement": "replacing",
                "placementTarget": "importExport",
            },
            "children": [
                {
                    "type": "Button",
                    "properties": {
                        "title": "Export Pipeline...",
                        "actionID": "file.export_pipeline",
                        "keyboardShortcut": {"key": "e", "modifiers": ["command"]},
                    },
                },
            ],
        },
    ]))

    # Create the initial window (with optional CLI args applied later)
    create_window(
        pipeline_path=getattr(_startup_args, "pipeline", None),
        image_path=getattr(_startup_args, "image", None),
    )


# --- Cleanup ---

@app.will_terminate
def on_terminate():
    for state in _window_states.values():
        state.cleanup()
    for path in plugin_json_paths.values():
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


# --- Entry Point ---

_startup_args = None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PillowUI — Image Transformation Pipeline Builder")
    parser.add_argument("--pipeline", "-p", help="Import a pipeline script (.py) at startup")
    parser.add_argument("--image", "-i", help="Open an image file at startup")
    _startup_args = parser.parse_args()

    app.run()

#!/usr/bin/env python3
"""PillowUI — Image Transformation Pipeline Builder"""

import json
import os
import sys
import importlib.util
import tempfile

import actionui
from PIL import Image

# --- View ID Constants ---
PIPELINE_TABLE_ID = 10
BTN_ADD_ID = 20
BTN_REMOVE_ID = 21
BTN_MOVE_UP_ID = 22
BTN_MOVE_DOWN_ID = 23
BTN_EXPORT_ID = 24
PLUGIN_PICKER_ID = 30

PREVIEW_IMAGE_ID = 50

PARAM_GROUP_ID = 60
LOADABLE_PARAMS_ID = 200

BTN_OPEN_ID = 80
BTN_SAVE_ID = 81

# --- Application State ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(SCRIPT_DIR, "plugins")

app = actionui.Application(name="PillowUI")
window = None

# Plugin registry: list of loaded plugin modules
plugin_registry = []  # [module, ...]
plugin_names = []     # [name, ...]
plugin_json_paths = {}  # {module: absolute_path_to_params_json}

# Pipeline: ordered list of steps
pipeline = []  # [{"plugin": module, "params": {name: value}, "enabled": True}, ...]

# Current state
source_image = None        # PIL.Image — original loaded image
processed_image = None     # PIL.Image — after pipeline
selected_pipeline_idx = -1 # Currently selected pipeline row
preview_temp_path = None   # Temp file for preview


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
                plugin_names.append(mod.PLUGIN_NAME)
        except Exception as e:
            print(f"Failed to load plugin {fname}: {e}", file=sys.stderr)


def get_default_params(plugin_mod):
    """Return a dict of default param values for a plugin."""
    params = {}
    for p in getattr(plugin_mod, "PLUGIN_PARAMS", []):
        params[p["name"]] = p["default"]
    return params


def generate_plugin_params_json(plugin_mod):
    """Generate an ActionUI JSON dict for a plugin's PLUGIN_PARAMS."""
    params_def = getattr(plugin_mod, "PLUGIN_PARAMS", [])
    # Invisible divider forces VStack to expand to full parent width.
    # Placed last with zero padding so it doesn't shift visible content.
    width_filler = {"type": "Divider", "properties": {"opacity": 0, "frame": {"height": 0}, "padding": 0}}

    if not params_def:
        return {
            "type": "VStack",
            "id": 1000,
            "properties": {
                "spacing": 8.0,
                "padding": "default",
                "alignment": "leading",
            },
            "children": [
                {
                    "type": "Text",
                    "properties": {
                        "text": "No parameters to configure",
                        "foregroundStyle": "secondary",
                    },
                },
                width_filler,
            ],
        }

    children = []
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

def execute_pipeline():
    """Run all enabled pipeline steps on the source image."""
    global processed_image
    if source_image is None:
        processed_image = None
        return
    img = source_image.copy()
    for step in pipeline:
        if not step["enabled"]:
            continue
        try:
            img = step["plugin"].transform(img, step["params"])
        except Exception as e:
            print(f"Plugin error ({step['plugin'].PLUGIN_NAME}): {e}", file=sys.stderr)
    processed_image = img


def update_preview():
    """Save processed image to temp file and update the Image view."""
    global preview_temp_path
    if window is None:
        return
    if processed_image is None:
        window.set_string(PREVIEW_IMAGE_ID, "photo")
        return
    if preview_temp_path is None:
        fd, preview_temp_path = tempfile.mkstemp(suffix=".png", prefix="pillowui_")
        os.close(fd)
    processed_image.save(preview_temp_path, "PNG")
    window.set_string(PREVIEW_IMAGE_ID, preview_temp_path)


def refresh_pipeline():
    """Re-execute pipeline and update preview."""
    execute_pipeline()
    update_preview()


# --- Table Sync ---

def sync_table():
    """Sync the pipeline table rows with the pipeline state."""
    if window is None:
        return
    rows = []
    for i, step in enumerate(pipeline):
        rows.append([
            str(i + 1),
            step["plugin"].PLUGIN_NAME,
        ])
    window.set_rows(PIPELINE_TABLE_ID, rows)


def update_toolbar_buttons():
    """Enable/disable toolbar buttons based on selection state."""
    if window is None:
        return
    has_selection = 0 <= selected_pipeline_idx < len(pipeline)
    window.set_property(BTN_REMOVE_ID, "disabled", not has_selection)
    window.set_property(BTN_MOVE_UP_ID, "disabled", not has_selection or selected_pipeline_idx <= 0)
    window.set_property(BTN_MOVE_DOWN_ID, "disabled", not has_selection or selected_pipeline_idx >= len(pipeline) - 1)


# --- Parameter UI ---

def show_params_for_step(step_idx):
    """Update the parameter panel to show controls for the selected pipeline step."""
    if window is None:
        return

    if step_idx < 0 or step_idx >= len(pipeline):
        window.set_property(PARAM_GROUP_ID, "title", "Parameters")
        window.set_string(LOADABLE_PARAMS_ID, os.path.join(PLUGINS_DIR, "empty_params.json"))
        return

    step = pipeline[step_idx]
    plugin_mod = step["plugin"]
    window.set_property(PARAM_GROUP_ID, "title", f"{plugin_mod.PLUGIN_NAME} Parameters")

    json_path = plugin_json_paths.get(plugin_mod, "")
    window.set_string(LOADABLE_PARAMS_ID, json_path)

    _sync_param_values(step_idx)


def _format_param_value(value, pdef):
    """Format a float param value for display in the text field."""
    step_val = pdef.get("step")
    if step_val is not None and step_val == int(step_val):
        return str(int(value))
    if abs(value) >= 100:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _sync_param_values(step_idx):
    """Set current param values on the dynamically loaded controls."""
    if window is None or step_idx < 0 or step_idx >= len(pipeline):
        return
    step = pipeline[step_idx]
    params_def = getattr(step["plugin"], "PLUGIN_PARAMS", [])
    control_id = 1001
    for pdef in params_def:
        value = step["params"].get(pdef["name"], pdef["default"])
        if pdef["type"] == "float":
            window.set_double(control_id, value)
            window.set_string(control_id + 1000, _format_param_value(value, pdef))
        elif pdef["type"] == "bool":
            window.set_bool(control_id, value)
        control_id += 1


# --- Export ---

def export_pipeline_script():
    """Generate a standalone Python script from the current pipeline."""
    imports = set()
    imports.add("from PIL import Image")
    code_lines = []

    for step in pipeline:
        if not step["enabled"]:
            continue
        imp = step["plugin"].export_imports()
        if imp:
            imports.add(imp)
        code = step["plugin"].export_code(step["params"])
        code_lines.append(f"# {step['plugin'].PLUGIN_NAME}")
        code_lines.append(code)

    script = '#!/usr/bin/env python3\n'
    script += '"""Generated by PillowUI"""\n\n'
    script += "import sys\n"
    script += "\n".join(sorted(imports)) + "\n\n"
    script += 'if len(sys.argv) < 3:\n'
    script += '    print("Usage: python pipeline.py input.png output.png")\n'
    script += '    sys.exit(1)\n\n'
    script += 'img = Image.open(sys.argv[1])\n\n'
    for line in code_lines:
        script += line + "\n"
    script += '\nimg.save(sys.argv[2])\n'
    script += 'print(f"Saved to {sys.argv[2]}")\n'

    return script


# --- Action Handlers ---

@app.action("image.open")
def on_image_open(ctx):
    global source_image
    paths = app.open_panel(
        title="Open Image",
        prompt="Open",
        allowed_types=["public.image"],
    )
    if not paths:
        return
    try:
        source_image = Image.open(paths[0])
    except Exception as e:
        print(f"Failed to open image: {e}", file=sys.stderr)
        return
    window.set_property(BTN_SAVE_ID, "disabled", False)
    refresh_pipeline()


@app.action("image.save")
def on_image_save(ctx):
    if processed_image is None:
        return
    path = app.save_panel(
        title="Save Image",
        prompt="Save",
        filename="output.png",
        allowed_types=["png", "jpg", "jpeg", "tiff", "bmp"],
    )
    if not path:
        return
    try:
        processed_image.save(path)
    except Exception as e:
        print(f"Failed to save image: {e}", file=sys.stderr)


@app.action("pipeline.add")
def on_pipeline_add(ctx):
    global selected_pipeline_idx
    if not plugin_registry:
        return
    # Get selected plugin from picker
    tag = window.get_string(PLUGIN_PICKER_ID)
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
    pipeline.append(step)
    sync_table()
    update_toolbar_buttons()
    refresh_pipeline()


@app.action("pipeline.remove")
def on_pipeline_remove(ctx):
    global selected_pipeline_idx
    if selected_pipeline_idx < 0 or selected_pipeline_idx >= len(pipeline):
        return
    pipeline.pop(selected_pipeline_idx)
    if selected_pipeline_idx >= len(pipeline):
        selected_pipeline_idx = len(pipeline) - 1
    sync_table()
    show_params_for_step(selected_pipeline_idx)
    update_toolbar_buttons()
    refresh_pipeline()


@app.action("pipeline.move.up")
def on_pipeline_move_up(ctx):
    global selected_pipeline_idx
    idx = selected_pipeline_idx
    if idx <= 0 or idx >= len(pipeline):
        return
    pipeline[idx], pipeline[idx - 1] = pipeline[idx - 1], pipeline[idx]
    selected_pipeline_idx = idx - 1
    sync_table()
    update_toolbar_buttons()
    refresh_pipeline()


@app.action("pipeline.move.down")
def on_pipeline_move_down(ctx):
    global selected_pipeline_idx
    idx = selected_pipeline_idx
    if idx < 0 or idx >= len(pipeline) - 1:
        return
    pipeline[idx], pipeline[idx + 1] = pipeline[idx + 1], pipeline[idx]
    selected_pipeline_idx = idx + 1
    sync_table()
    update_toolbar_buttons()
    refresh_pipeline()


@app.action("pipeline.selection.changed")
def on_pipeline_selection_changed(ctx):
    global selected_pipeline_idx
    selected_row = window.get_value(PIPELINE_TABLE_ID)
    if selected_row is None or len(selected_row) == 0:
        selected_pipeline_idx = -1
    else:
        # First column is the row number
        try:
            selected_pipeline_idx = int(selected_row[0]) - 1
        except (ValueError, TypeError, IndexError):
            selected_pipeline_idx = -1
    show_params_for_step(selected_pipeline_idx)
    update_toolbar_buttons()


@app.action("pipeline.export")
def on_pipeline_export(ctx):
    if not pipeline:
        return
    script = export_pipeline_script()
    path = app.save_panel(
        title="Export Pipeline Script",
        prompt="Export",
        filename="pipeline.py",
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


@app.action("plugin.picker.changed")
def on_plugin_picker_changed(ctx):
    # Just updates the picker selection state; add happens via "+" button
    pass


# Default action handler for dynamically loaded param controls
def on_dynamic_param_changed(ctx):
    action = ctx.action_id
    if not action.startswith("param."):
        return

    # Determine if this is a text field change or a slider/toggle change
    is_text = action.endswith(".text.changed")
    if is_text:
        param_name = action[len("param."):-len(".text.changed")]
    elif action.endswith(".changed"):
        param_name = action[len("param."):-len(".changed")]
    else:
        return

    if selected_pipeline_idx < 0 or selected_pipeline_idx >= len(pipeline):
        return
    step = pipeline[selected_pipeline_idx]
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
                    text_val = window.get_string(text_field_id)
                    if text_val is not None:
                        try:
                            value = float(text_val)
                            pmin = pdef.get("min", 0.0)
                            pmax = pdef.get("max", 1.0)
                            value = max(pmin, min(pmax, value))
                            step["params"][param_name] = value
                            window.set_double(slider_id, value)
                        except ValueError:
                            pass
                else:
                    # Slider changed — update text field and param
                    value = window.get_double(slider_id)
                    if value is not None:
                        step["params"][param_name] = value
                        window.set_string(text_field_id, _format_param_value(value, pdef))
            elif pdef["type"] == "bool" and not is_text:
                value = window.get_bool(ctx.view_id)
                if value is not None:
                    step["params"][param_name] = value
            refresh_pipeline()
            return
        control_id += 1


# --- Lifecycle ---

@app.did_finish_launching
def on_launch():
    global window
    load_plugins()
    generate_all_plugin_json()
    app.set_default_handler(on_dynamic_param_changed)
    json_path = os.path.join(SCRIPT_DIR, "PillowUI.json")
    window = app.load_and_present_window(json_path, title="PillowUI")

    # Load empty params view initially
    window.set_string(LOADABLE_PARAMS_ID, os.path.join(PLUGINS_DIR, "empty_params.json"))

    # Populate plugin picker
    if plugin_names:
        options = [{"title": name, "tag": str(i + 1)} for i, name in enumerate(plugin_names)]
        window.set_property(PLUGIN_PICKER_ID, "options", options)
        window.set_string(PLUGIN_PICKER_ID, "1")


# --- Cleanup ---

@app.will_terminate
def on_terminate():
    if preview_temp_path and os.path.exists(preview_temp_path):
        try:
            os.unlink(preview_temp_path)
        except OSError:
            pass
    for path in plugin_json_paths.values():
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


# --- Entry Point ---

if __name__ == "__main__":
    app.run()

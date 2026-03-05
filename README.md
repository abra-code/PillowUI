# PillowUI

A macOS image transformation pipeline builder powered by [ActionUI](https://github.com/nicetomeetyou1/ActionUI) and [Pillow](https://pillow.readthedocs.io/).

Load an image, stack transformation plugins in any order, tweak parameters in real time, and preview the result. When satisfied, export the pipeline as a standalone Python script.

## Dependencies

- **macOS 14.6+** (arm64 or x86_64)
- **Python 3.8+** with development headers (`python3-config` must work)
- **Xcode** with command-line tools
- **Pillow** — `pip3 install Pillow`
- **actionui** — the ActionUI Python module. It programmatically creates, configures, and launches a native macOS app with SwiftUI views defined via JSON.

## Installation

### 1. Install Pillow

```bash
pip3 install Pillow
```

### 2. Build and install the actionui Python module

The `actionui` module is not published as a pip package. You need to build it from the [ActionUI](https://github.com/abra-code/ActionUI) sources.

Clone or download the ActionUI repository, then build the three required static frameworks (ActionUI, ActionUICAdapter, ActionUIAppKitApplication) in Xcode with `BUILD_LIBRARY_FOR_DISTRIBUTION=YES`. Copy the resulting `.framework` bundles into `ActionUIPython/frameworks/`.

Then from the `ActionUIPython` directory:

```bash
pip3 install --no-cache-dir --verbose .
```

See [ActionUIPython/BUILD_GUIDE.md](https://github.com/abra-code/ActionUI/blob/main/ActionUIPython/BUILD_GUIDE.md) for full details.

### 3. Run PillowUI

```bash
python3 PillowUI.py
```

## Included Plugins

Brightness, Contrast, Gaussian Blur, Grayscale, Resize, Rotate, Sharpness, Color (Saturation), Flip, Invert, Auto Contrast, Equalize, Posterize, Solarize, Emboss, Find Edges, Unsharp Mask, Crop.

## Technical Design

### Plugin System

Plugins live in the `plugins/` directory. Each plugin is a Python module exporting:

- `PLUGIN_NAME` — display name
- `PLUGIN_PARAMS` — list of parameter definitions (type, default, min/max, label)
- `transform(image, params)` — receives a PIL Image and returns the transformed Image
- `export_code(params)` / `export_imports()` — for standalone script generation

Plugins are discovered at launch by scanning `plugins/` for `.py` files (excluding `_`-prefixed). The app loads them via `importlib` and registers any module that has both `PLUGIN_NAME` and `transform`.

### Pipeline

The pipeline is an ordered list of steps. Each step references a plugin module with its own parameter values. The full pipeline executes sequentially on the source image — each step's output feeds the next step's input.

### Dynamically Loaded Plugin Settings

Plugin parameter UIs are generated at runtime from `PLUGIN_PARAMS` definitions:

1. **ActionUI JSON generation** — At launch, `generate_plugin_params_json()` converts each plugin's `PLUGIN_PARAMS` into an ActionUI JSON layout file (`{plugin}_params.json`). Float params become `[Label | Slider | TextField]` rows; bool params become Toggles. These files are written to `plugins/` and cleaned up on exit.

2. **ActionUI LoadableView** — The main window JSON contains a `LoadableView` (a container that loads its content from a JSON file at runtime). When the user selects a pipeline step, the app points the LoadableView at that plugin's generated JSON file via `set_string()`. ActionUI parses the JSON and renders native SwiftUI controls.

3. **Bidirectional sync** — Sliders and TextFields are wired with `valueChangeActionID` actions. Moving a slider updates the adjacent TextField; editing the TextField updates the slider position (with min/max clamping). Both paths update the pipeline step's parameter value and re-execute the pipeline.

4. **ID scheme** — Slider IDs start at 1001 and increment per parameter. Corresponding TextField IDs are offset by +1000 (2001, 2002, ...). This allows the action handler to locate both controls for any parameter without collision.

# PillowUI

![PillowUI Icon](Pillow.png)

A macOS image transformation pipeline builder powered by [ActionUI](https://github.com/abra-code/ActionUI) and [Pillow](https://pillow.readthedocs.io/).

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

Clone or download the ActionUI repository, then run the build script:

```bash
cd ActionUI/ActionUIPython
./build_and_install.sh
```

This builds the required static frameworks as Release universal (arm64 + x86_64) via xcodebuild and installs the `actionui` Python module with pip.

See [ActionUIPython/BUILD_GUIDE.md](https://github.com/abra-code/ActionUI/blob/main/ActionUIPython/BUILD_GUIDE.md) for manual build steps and details.

### 3. Run PillowUI

```bash
python3 PillowUI.py
```

## Usage

### Pipeline

The pipeline is an ordered list of steps. Each step references a plugin module with its own parameter values. The full pipeline executes sequentially on the source image — each step's output feeds the next step's input.

### Export & Import

**Export** generates a standalone `.py` script that reproduces the current pipeline using only Pillow — no PillowUI or ActionUI dependency required. The script includes all transformation steps with their parameter values baked in, plus output format and quality settings.

**Import** lets you load a previously exported `.py` pipeline back into PillowUI. All steps, parameter values, output format, and quality settings are restored, so you can review, tweak, and re-export the pipeline.

## Included Plugins

- **Auto Contrast** — Normalize image contrast automatically
- **Border** — Add a solid-color border around the image
- **Box Blur** — Apply box blur (average of neighboring pixels)
- **Brightness** — Adjust image brightness
- **Color Saturation** — Adjust image color saturation
- **Color Temperature** — Shift color temperature warm or cool via per-channel LUTs
- **Colorize** — Map grayscale values to a two-color gradient (tinting effect)
- **Contour** — Trace contours to create a line-drawing effect
- **Contrast** — Adjust image contrast
- **Crop** — Crop image by percentage from each edge
- **Detail** — Enhance fine detail in the image
- **Edge Enhance** — Subtly enhance edges while preserving the image
- **Emboss** — Apply 3D embossed effect
- **Equalize** — Histogram equalization for uniform tonal distribution
- **Find Edges** — Detect and highlight edges in the image
- **Flip** — Mirror image horizontally or vertically
- **Gaussian Blur** — Apply Gaussian blur
- **Grayscale** — Convert image to grayscale
- **Invert** — Negate all pixel values
- **Max Filter** — Pick the brightest pixel in each neighborhood (dilate bright features)
- **Median Filter** — Reduce noise by replacing each pixel with the median of its neighbors
- **Min Filter** — Pick the darkest pixel in each neighborhood (erode bright features)
- **Mode Filter** — Replace each pixel with the most frequent value in its neighborhood
- **Pad** — Resize image to fit within a target size, padding the remainder
- **Posterize** — Reduce color depth by limiting bits per channel
- **Quantize** — Reduce to a limited number of colors (palette effect)
- **Resize** — Resize image by percentage
- **Rotate** — Rotate image by angle
- **Self Blend** — Blend the image with itself using Multiply or Screen
- **Sharpen (Filter)** — Convolution-based sharpening (different from enhancement sharpness)
- **Sharpness** — Adjust image sharpness
- **Smooth** — Apply light smoothing to reduce noise
- **Solarize** — Invert pixels above a brightness threshold
- **Spread** — Randomly displace pixels for a frosted-glass effect
- **Text Watermark** — Overlay text on the image
- **Threshold** — Convert to binary black & white using a brightness cutoff
- **Unsharp Mask** — Professional sharpening with radius, strength, and threshold

Each plugin can be added to the pipeline multiple times with different settings (e.g., two watermarks at different positions).

## Technical Design

### Plugin System

Plugins live in the `plugins/` directory. Each plugin is a Python module exporting:

- `PLUGIN_NAME` — display name
- `PLUGIN_PARAMS` — list of parameter definitions (type, default, min/max, label)
- `transform(image, params)` — receives a PIL Image and returns the transformed Image
- `export_code(params)` / `export_imports()` — for standalone script generation

Plugins are discovered at launch by scanning `plugins/` for `.py` files (excluding `_`-prefixed). The app loads them via `importlib` and registers any module that has both `PLUGIN_NAME` and `transform`.

### Dynamically Loaded Plugin Settings

Plugin parameter UIs are generated at runtime from `PLUGIN_PARAMS` definitions:

1. **ActionUI JSON generation** — At launch, `generate_plugin_params_json()` converts each plugin's `PLUGIN_PARAMS` into an ActionUI JSON layout file (`{plugin}_params.json`). Float params become `[Label | Slider | TextField]` rows; bool params become Toggles. These files are written to `plugins/` and cleaned up on exit.

2. **ActionUI LoadableView** — The main window JSON contains a `LoadableView` (a container that loads its content from a JSON file at runtime). When the user selects a pipeline step, the app points the LoadableView at that plugin's generated JSON file via `set_string()`. ActionUI parses the JSON and renders native SwiftUI controls.

3. **Bidirectional sync** — Sliders and TextFields are wired with `valueChangeActionID` actions. Moving a slider updates the adjacent TextField; editing the TextField updates the slider position (with min/max clamping). Both paths update the pipeline step's parameter value and re-execute the pipeline.

4. **ID scheme** — Slider IDs start at 1001 and increment per parameter. Corresponding TextField IDs are offset by +1000 (2001, 2002, ...). This allows the action handler to locate both controls for any parameter without collision.

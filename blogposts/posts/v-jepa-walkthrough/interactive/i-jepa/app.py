# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.23.14",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="I-JEPA input image")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import base64
    import hashlib
    import html
    import math
    import random
    import sys

    return base64, hashlib, html, math, random, sys


@app.cell
def _(base64, html, mo, sys):
    IMAGE_WIDTH = 1254
    IMAGE_HEIGHT = 1254
    OUTPUT_SIZE = 224

    if sys.platform == "emscripten":
        # From interactive/i-jepa/dist/index.html to the post's shared assets.
        _image_src = "../../../assets/cat.png"
    else:
        _image_path = mo.notebook_location().parents[1] / "assets" / "cat.png"
        _encoded_image = base64.b64encode(_image_path.read_bytes()).decode("ascii")
        _image_src = f"data:image/png;base64,{_encoded_image}"

    image_src = html.escape(_image_src, quote=True)
    return IMAGE_HEIGHT, IMAGE_WIDTH, OUTPUT_SIZE, image_src


@app.cell
def _(mo):
    area_fraction = mo.ui.slider(
        start=0.30,
        stop=1.00,
        step=0.01,
        value=0.50,
        debounce=True,
        show_value=True,
        include_input=True,
        label="Area fraction a",
        full_width=True,
    )
    aspect_ratio = mo.ui.slider(
        start=0.75,
        stop=4 / 3,
        step=0.01,
        value=1.00,
        debounce=True,
        show_value=True,
        include_input=True,
        label="Aspect ratio r",
        full_width=True,
    )
    sample_position = mo.ui.button(
        value=0,
        on_click=lambda draw: draw + 1,
        label="New position",
        kind="neutral",
        full_width=True,
    )
    return area_fraction, aspect_ratio, sample_position


@app.cell
def _(
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    area_fraction,
    aspect_ratio,
    hashlib,
    math,
    random,
    sample_position,
):
    _target_area = area_fraction.value * IMAGE_HEIGHT * IMAGE_WIDTH
    _crop_width = round(math.sqrt(_target_area * aspect_ratio.value))
    _crop_height = round(math.sqrt(_target_area / aspect_ratio.value))
    _valid = _crop_width <= IMAGE_WIDTH and _crop_height <= IMAGE_HEIGHT

    if _valid:
        _seed_material = (
            f"{area_fraction.value:.4f}:{aspect_ratio.value:.4f}:"
            f"{sample_position.value}"
        ).encode("utf-8")
        _seed = int.from_bytes(
            hashlib.blake2b(_seed_material, digest_size=8).digest(), "big"
        )
        _rng = random.Random(_seed)
        _left = _rng.randint(0, IMAGE_WIDTH - _crop_width)
        _top = _rng.randint(0, IMAGE_HEIGHT - _crop_height)
    else:
        _left = None
        _top = None

    crop = {
        "area_fraction": area_fraction.value,
        "aspect_ratio": aspect_ratio.value,
        "target_area": _target_area,
        "width": _crop_width,
        "height": _crop_height,
        "valid": _valid,
        "left": _left,
        "top": _top,
    }
    return (crop,)


@app.cell(hide_code=True)
def _(
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    area_fraction,
    aspect_ratio,
    crop,
    image_src,
    mo,
    sample_position,
):
    if crop["valid"]:
        _overlay = f"""
          <svg class="ij-crop-overlay" viewBox="0 0 {IMAGE_WIDTH} {IMAGE_HEIGHT}" aria-hidden="true">
            <defs>
              <mask id="ij-crop-window">
                <rect width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}" fill="white"></rect>
                <rect x="{crop['left']}" y="{crop['top']}" width="{crop['width']}" height="{crop['height']}" fill="black"></rect>
              </mask>
            </defs>
            <rect width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}" class="ij-crop-dim" mask="url(#ij-crop-window)"></rect>
            <rect x="{crop['left']}" y="{crop['top']}" width="{crop['width']}" height="{crop['height']}" class="ij-crop-box"></rect>
          </svg>
        """
        _calculation = f"""
          <div class="ij-calculation">
            <div>T = aHW = {crop['area_fraction']:.2f} × {IMAGE_HEIGHT:,} × {IMAGE_WIDTH:,} = {crop['target_area']:,.0f} px²</div>
            <div>w = round(√(Tr)) = {crop['width']:,} px &nbsp;·&nbsp; h = round(√(T/r)) = {crop['height']:,} px</div>
            <div>sampled (top, left) = ({crop['top']:,}, {crop['left']:,})</div>
          </div>
        """
        _alt = (
            f"The cat image with a {crop['width']} by {crop['height']} pixel crop "
            f"starting at top {crop['top']} and left {crop['left']}."
        )
    else:
        _overlay = ""
        _calculation = f"""
          <div class="ij-calculation ij-rejected">
            <div>T = aHW = {crop['area_fraction']:.2f} × {IMAGE_HEIGHT:,} × {IMAGE_WIDTH:,} = {crop['target_area']:,.0f} px²</div>
            <div>w = {crop['width']:,} px &nbsp;·&nbsp; h = {crop['height']:,} px</div>
            <div>This rectangle does not fit inside the input, so the sampler would reject this draw.</div>
          </div>
        """
        _alt = "The cat input image; the selected crop geometry is too large to fit."

    _visual = mo.Html(
        f"""
        <style>
          #ij-input-size {{
            --ij-dimension: #2f5d8c;
            --ij-muted: #5f6368;
            --ij-border: #d7d9dc;
            --ij-crop: #cf4f24;
            --ij-rejected: #a33a31;
            box-sizing: border-box;
            color: inherit;
            margin: 0 auto;
            max-width: 680px;
            padding: 0.5rem;
            width: 100%;
          }}

          #ij-input-size * {{
            box-sizing: border-box;
          }}

          #ij-input-size .ij-width {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            gap: 0.65rem;
            margin: 0 0 0.45rem 2.25rem;
          }}

          #ij-input-size .ij-width::before,
          #ij-input-size .ij-width::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            height: 1px;
          }}

          #ij-input-size .ij-dimension-label {{
            font-size: 0.9rem;
            font-variant-numeric: tabular-nums;
            font-weight: 500;
            white-space: nowrap;
          }}

          #ij-input-size .ij-image-row {{
            align-items: stretch;
            display: grid;
            gap: 0.55rem;
            grid-template-columns: 1.7rem minmax(0, 1fr);
          }}

          #ij-input-size .ij-height {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            gap: 0.65rem;
            justify-content: center;
            writing-mode: vertical-rl;
          }}

          #ij-input-size .ij-height::before,
          #ij-input-size .ij-height::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            width: 1px;
          }}

          #ij-input-size img {{
            border: 1px solid var(--ij-border);
            display: block;
            height: auto;
            max-width: 100%;
            width: 100%;
          }}

          #ij-input-size .ij-image-stage {{
            position: relative;
          }}

          #ij-input-size .ij-crop-overlay {{
            display: block;
            height: 100%;
            inset: 0;
            position: absolute;
            width: 100%;
          }}

          #ij-input-size .ij-crop-dim {{
            fill: rgb(0 0 0 / 45%);
          }}

          #ij-input-size .ij-crop-box {{
            fill: none;
            stroke: var(--ij-crop);
            stroke-width: 9;
            vector-effect: non-scaling-stroke;
          }}

          #ij-input-size figcaption {{
            color: var(--ij-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.88rem;
            margin: 0.6rem 0 0 2.25rem;
            text-align: center;
          }}

          #ij-input-size .ij-calculation {{
            color: var(--ij-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.84rem;
            line-height: 1.55;
            margin: 0.7rem 0 0 2.25rem;
            text-align: center;
          }}

          #ij-input-size .ij-rejected {{
            color: var(--ij-rejected);
          }}

          @media (max-width: 420px) {{
            #ij-input-size {{
              padding: 0.25rem;
            }}

            #ij-input-size .ij-width {{
              margin-left: 1.8rem;
            }}

            #ij-input-size .ij-image-row {{
              gap: 0.35rem;
              grid-template-columns: 1.45rem minmax(0, 1fr);
            }}

            #ij-input-size figcaption {{
              margin-left: 1.8rem;
            }}

            #ij-input-size .ij-calculation {{
              margin-left: 1.8rem;
            }}
          }}

          @media (prefers-color-scheme: dark) {{
            #ij-input-size {{
              --ij-dimension: #9bc3ec;
              --ij-muted: #b8bdc3;
              --ij-border: #555a60;
              --ij-crop: #ff9a68;
              --ij-rejected: #ff9990;
            }}
          }}
        </style>

        <figure id="ij-input-size">
          <div class="ij-width" aria-hidden="true">
            <span class="ij-dimension-label">width = {IMAGE_WIDTH:,} px</span>
          </div>
          <div class="ij-image-row">
            <div class="ij-height" aria-hidden="true">
              <span class="ij-dimension-label">height = {IMAGE_HEIGHT:,} px</span>
            </div>
            <div class="ij-image-stage">
              <img
                src="{image_src}"
                width="{IMAGE_WIDTH}"
                height="{IMAGE_HEIGHT}"
                alt="{_alt}"
              >
              {_overlay}
            </div>
          </div>
          <figcaption>shape = (height, width) = ({IMAGE_HEIGHT:,}, {IMAGE_WIDTH:,})</figcaption>
          {_calculation}
        </figure>
        """
    )
    _controls = mo.vstack(
        [
            mo.hstack(
                [area_fraction, aspect_ratio],
                widths="equal",
                wrap=True,
                align="end",
                gap=0.8,
            ),
            sample_position,
        ],
        gap=0.55,
    )
    mo.vstack([_controls, _visual], gap=0.8).style(
        {"max-width": "680px", "margin": "0 auto", "padding": "0.5rem"}
    )
    return


@app.cell(hide_code=True)
def _(IMAGE_HEIGHT, IMAGE_WIDTH, OUTPUT_SIZE, crop, image_src, mo):
    if crop["valid"]:
        _resize_content = f"""
          <svg class="ij-image-defs" aria-hidden="true">
            <defs>
              <image id="ij-resize-cat-source" href="{image_src}" width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}"></image>
            </defs>
          </svg>

          <div class="ij-resize-part">
            <div class="ij-part-label">sampled crop</div>
            <svg
              class="ij-sample-frame"
              style="aspect-ratio: {crop['width']} / {crop['height']};"
              viewBox="{crop['left']} {crop['top']} {crop['width']} {crop['height']}"
              preserveAspectRatio="none"
              role="img"
              aria-label="The sampled crop before resizing; it is {crop['width']} pixels wide and {crop['height']} pixels high."
            >
              <use href="#ij-resize-cat-source"></use>
            </svg>
            <div class="ij-shape">{crop['width']:,} × {crop['height']:,} px</div>
          </div>

          <div class="ij-resize-transition" aria-label="Resize the sampled crop to {OUTPUT_SIZE} by {OUTPUT_SIZE} pixels">
            <span>resize</span>
            <span class="ij-arrow ij-arrow-right" aria-hidden="true">→</span>
            <span class="ij-arrow ij-arrow-down" aria-hidden="true">↓</span>
          </div>

          <div class="ij-resize-part ij-output-part">
            <div class="ij-part-label">resized sample</div>
            <div class="ij-output-width" aria-hidden="true">
              <span>{OUTPUT_SIZE} px</span>
            </div>
            <div class="ij-output-row">
              <div class="ij-output-height" aria-hidden="true">
                <span>{OUTPUT_SIZE} px</span>
              </div>
              <svg
                class="ij-output-image"
                viewBox="{crop['left']} {crop['top']} {crop['width']} {crop['height']}"
                preserveAspectRatio="none"
                role="img"
                aria-label="The sampled crop resized to {OUTPUT_SIZE} pixels wide and {OUTPUT_SIZE} pixels high."
              >
                <use href="#ij-resize-cat-source"></use>
              </svg>
            </div>
            <div class="ij-shape">{OUTPUT_SIZE} × {OUTPUT_SIZE} px</div>
          </div>
        """
    else:
        _resize_content = """
          <p class="ij-no-resize">No sample is resized because the current crop geometry would be rejected.</p>
        """

    mo.Html(
        f"""
        <style>
          #ij-resize-step {{
            --ij-dimension: #2f5d8c;
            --ij-muted: #5f6368;
            --ij-border: #d7d9dc;
            --ij-rejected: #a33a31;
            align-items: center;
            box-sizing: border-box;
            display: grid;
            gap: 1.1rem;
            grid-template-columns: minmax(260px, 1fr) 5rem 15.5rem;
            margin: 0 auto;
            max-width: 820px;
            padding: 0.75rem;
            width: 100%;
          }}

          #ij-resize-step * {{
            box-sizing: border-box;
          }}

          #ij-resize-step .ij-resize-part {{
            min-width: 0;
            text-align: center;
          }}

          #ij-resize-step .ij-image-defs {{
            height: 0;
            overflow: hidden;
            position: absolute;
            width: 0;
          }}

          #ij-resize-step .ij-part-label {{
            color: var(--ij-muted);
            font-size: 0.82rem;
            font-weight: 500;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
          }}

          #ij-resize-step .ij-sample-frame {{
            border: 1px solid var(--ij-border);
            display: block;
            margin: 0 auto;
            max-height: 320px;
            max-width: 360px;
            width: 100%;
          }}

          #ij-resize-step .ij-output-image {{
            border: 1px solid var(--ij-border);
            display: block;
          }}

          #ij-resize-step .ij-shape {{
            color: var(--ij-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.84rem;
            margin-top: 0.45rem;
          }}

          #ij-resize-step .ij-resize-transition {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            flex-direction: column;
            font-size: 0.84rem;
            font-weight: 500;
            gap: 0.15rem;
            justify-content: center;
          }}

          #ij-resize-step .ij-arrow {{
            font-size: 2rem;
            line-height: 1;
          }}

          #ij-resize-step .ij-arrow-down {{
            display: none;
          }}

          #ij-resize-step .ij-output-width {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            font-size: 0.78rem;
            gap: 0.45rem;
            margin: 0 auto 0.35rem 1.6rem;
            width: {OUTPUT_SIZE}px;
          }}

          #ij-resize-step .ij-output-width::before,
          #ij-resize-step .ij-output-width::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            height: 1px;
          }}

          #ij-resize-step .ij-output-row {{
            display: grid;
            gap: 0.35rem;
            grid-template-columns: 1.25rem {OUTPUT_SIZE}px;
            justify-content: center;
          }}

          #ij-resize-step .ij-output-height {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            font-size: 0.78rem;
            gap: 0.45rem;
            justify-content: center;
            writing-mode: vertical-rl;
          }}

          #ij-resize-step .ij-output-height::before,
          #ij-resize-step .ij-output-height::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            width: 1px;
          }}

          #ij-resize-step .ij-output-image {{
            height: {OUTPUT_SIZE}px;
            width: {OUTPUT_SIZE}px;
          }}

          #ij-resize-step .ij-no-resize {{
            color: var(--ij-rejected);
            grid-column: 1 / -1;
            margin: 0;
            text-align: center;
          }}

          @media (max-width: 680px) {{
            #ij-resize-step {{
              grid-template-columns: minmax(0, 1fr);
              justify-items: center;
            }}

            #ij-resize-step .ij-resize-part {{
              width: 100%;
            }}

            #ij-resize-step .ij-resize-transition {{
              min-height: 3.25rem;
            }}

            #ij-resize-step .ij-arrow-right {{
              display: none;
            }}

            #ij-resize-step .ij-arrow-down {{
              display: inline;
            }}
          }}

          @media (prefers-color-scheme: dark) {{
            #ij-resize-step {{
              --ij-dimension: #9bc3ec;
              --ij-muted: #b8bdc3;
              --ij-border: #555a60;
              --ij-rejected: #ff9990;
            }}
          }}
        </style>

        <section id="ij-resize-step" aria-label="Resize the sampled crop to a fixed 224 by 224 input">
          {_resize_content}
        </section>
        """
    )
    return


@app.cell(hide_code=True)
def _(IMAGE_HEIGHT, IMAGE_WIDTH, OUTPUT_SIZE, crop, image_src, mo):
    PATCH_SIZE = 14
    GRID_SIZE = OUTPUT_SIZE // PATCH_SIZE

    if crop["valid"]:
        _vertical_lines = " ".join(
            f"M {column * PATCH_SIZE} 0 V {OUTPUT_SIZE}"
            for column in range(1, GRID_SIZE)
        )
        _horizontal_lines = " ".join(
            f"M 0 {row * PATCH_SIZE} H {OUTPUT_SIZE}"
            for row in range(1, GRID_SIZE)
        )
        _grid_path = f"{_vertical_lines} {_horizontal_lines}"
        _highlight_column = 7
        _highlight_row = 6
        _grid_content = f"""
          <div class="ij-grid-width" aria-hidden="true">
            <span>{GRID_SIZE} columns × {PATCH_SIZE} px = {OUTPUT_SIZE} px</span>
          </div>
          <div class="ij-grid-row">
            <div class="ij-grid-height" aria-hidden="true">
              <span>{GRID_SIZE} rows × {PATCH_SIZE} px = {OUTPUT_SIZE} px</span>
            </div>
            <svg
              class="ij-grid-image"
              viewBox="0 0 {OUTPUT_SIZE} {OUTPUT_SIZE}"
              role="img"
              aria-label="The resized cat sample divided into a sixteen by sixteen grid of fourteen by fourteen pixel patches."
            >
              <defs>
                <image id="ij-grid-cat-source" href="{image_src}" width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}"></image>
              </defs>
              <svg
                width="{OUTPUT_SIZE}"
                height="{OUTPUT_SIZE}"
                viewBox="{crop['left']} {crop['top']} {crop['width']} {crop['height']}"
                preserveAspectRatio="none"
              >
                <use href="#ij-grid-cat-source"></use>
              </svg>
              <path d="{_grid_path}" class="ij-grid-shadow"></path>
              <path d="{_grid_path}" class="ij-grid-lines"></path>
              <rect x="0" y="0" width="{OUTPUT_SIZE}" height="{OUTPUT_SIZE}" class="ij-grid-border"></rect>
              <rect
                x="{_highlight_column * PATCH_SIZE}"
                y="{_highlight_row * PATCH_SIZE}"
                width="{PATCH_SIZE}"
                height="{PATCH_SIZE}"
                class="ij-highlight-patch"
              ></rect>
            </svg>
          </div>
          <div class="ij-grid-summary">
            {GRID_SIZE} × {GRID_SIZE} = {GRID_SIZE * GRID_SIZE} patches &nbsp;·&nbsp; highlighted patch = {PATCH_SIZE} × {PATCH_SIZE} px
          </div>
        """
    else:
        _grid_content = """
          <p class="ij-no-grid">No patch grid is formed because the current crop geometry would be rejected.</p>
        """

    mo.Html(
        f"""
        <style>
          #ij-patch-grid {{
            --ij-dimension: #2f5d8c;
            --ij-muted: #5f6368;
            --ij-border: #d7d9dc;
            --ij-highlight: #cf4f24;
            --ij-rejected: #a33a31;
            box-sizing: border-box;
            margin: 0 auto;
            max-width: 540px;
            padding: 0.75rem;
            width: 100%;
          }}

          #ij-patch-grid * {{
            box-sizing: border-box;
          }}

          #ij-patch-grid .ij-grid-width {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            font-size: 0.8rem;
            gap: 0.55rem;
            margin: 0 0 0.4rem 1.65rem;
          }}

          #ij-patch-grid .ij-grid-width::before,
          #ij-patch-grid .ij-grid-width::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            height: 1px;
          }}

          #ij-patch-grid .ij-grid-row {{
            display: grid;
            gap: 0.4rem;
            grid-template-columns: 1.25rem minmax(0, 1fr);
          }}

          #ij-patch-grid .ij-grid-height {{
            align-items: center;
            color: var(--ij-dimension);
            display: flex;
            font-size: 0.8rem;
            gap: 0.55rem;
            justify-content: center;
            writing-mode: vertical-rl;
          }}

          #ij-patch-grid .ij-grid-height::before,
          #ij-patch-grid .ij-grid-height::after {{
            background: var(--ij-dimension);
            content: "";
            flex: 1;
            width: 1px;
          }}

          #ij-patch-grid .ij-grid-image {{
            display: block;
            height: auto;
            width: 100%;
          }}

          #ij-patch-grid .ij-grid-shadow {{
            fill: none;
            stroke: rgb(0 0 0 / 72%);
            stroke-width: 1.5;
            vector-effect: non-scaling-stroke;
          }}

          #ij-patch-grid .ij-grid-lines {{
            fill: none;
            stroke: rgb(255 255 255 / 82%);
            stroke-width: 0.65;
            vector-effect: non-scaling-stroke;
          }}

          #ij-patch-grid .ij-grid-border {{
            fill: none;
            stroke: rgb(0 0 0 / 82%);
            stroke-width: 1.5;
            vector-effect: non-scaling-stroke;
          }}

          #ij-patch-grid .ij-highlight-patch {{
            fill: rgb(207 79 36 / 22%);
            stroke: var(--ij-highlight);
            stroke-width: 2.5;
            vector-effect: non-scaling-stroke;
          }}

          #ij-patch-grid .ij-grid-summary {{
            color: var(--ij-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.84rem;
            margin: 0.55rem 0 0 1.65rem;
            text-align: center;
          }}

          #ij-patch-grid .ij-no-grid {{
            color: var(--ij-rejected);
            margin: 0;
            text-align: center;
          }}

          @media (max-width: 420px) {{
            #ij-patch-grid {{
              padding: 0.4rem;
            }}

            #ij-patch-grid .ij-grid-width,
            #ij-patch-grid .ij-grid-summary {{
              margin-left: 1.45rem;
            }}

            #ij-patch-grid .ij-grid-width,
            #ij-patch-grid .ij-grid-height {{
              font-size: 0.72rem;
            }}
          }}

          @media (prefers-color-scheme: dark) {{
            #ij-patch-grid {{
              --ij-dimension: #9bc3ec;
              --ij-muted: #b8bdc3;
              --ij-border: #555a60;
              --ij-highlight: #ff9a68;
              --ij-rejected: #ff9990;
            }}
          }}
        </style>

        <section id="ij-patch-grid" aria-label="View the resized sample as image patches">
          {_grid_content}
        </section>
        """
    )
    return


@app.cell
def _(mo):
    target_area_fraction = mo.ui.slider(
        start=0.15,
        stop=0.20,
        step=0.01,
        value=0.18,
        debounce=True,
        show_value=True,
        include_input=True,
        label="Target-block area fraction",
        full_width=True,
    )
    target_aspect_ratio = mo.ui.slider(
        start=0.75,
        stop=1.50,
        step=0.05,
        value=1.00,
        debounce=True,
        show_value=True,
        include_input=True,
        label="Target aspect ratio (height ÷ width)",
        full_width=True,
    )
    context_area_fraction = mo.ui.slider(
        start=0.85,
        stop=1.00,
        step=0.01,
        value=0.90,
        debounce=True,
        show_value=True,
        include_input=True,
        label="Context-block area fraction",
        full_width=True,
    )
    sample_masks = mo.ui.button(
        value=0,
        on_click=lambda draw: draw + 1,
        label="New locations",
        kind="neutral",
        full_width=True,
    )
    return (
        context_area_fraction,
        sample_masks,
        target_area_fraction,
        target_aspect_ratio,
    )


@app.cell
def _(
    context_area_fraction,
    hashlib,
    math,
    random,
    sample_masks,
    target_area_fraction,
    target_aspect_ratio,
):
    _grid_size = 16
    _number_of_targets = 4

    _target_budget = int(
        _grid_size * _grid_size * target_area_fraction.value
    )
    _target_height = round(
        math.sqrt(_target_budget * target_aspect_ratio.value)
    )
    _target_width = round(
        math.sqrt(_target_budget / target_aspect_ratio.value)
    )
    while _target_height >= _grid_size:
        _target_height -= 1
    while _target_width >= _grid_size:
        _target_width -= 1

    _context_budget = int(
        _grid_size * _grid_size * context_area_fraction.value
    )
    _context_height = round(math.sqrt(_context_budget))
    _context_width = round(math.sqrt(_context_budget))
    while _context_height >= _grid_size:
        _context_height -= 1
    while _context_width >= _grid_size:
        _context_width -= 1

    _seed_material = (
        f"{target_area_fraction.value:.4f}:"
        f"{target_aspect_ratio.value:.4f}:"
        f"{context_area_fraction.value:.4f}:"
        f"{sample_masks.value}"
    ).encode("utf-8")
    _seed = int.from_bytes(
        hashlib.blake2b(_seed_material, digest_size=8).digest(), "big"
    )
    _rng = random.Random(_seed)

    def _rectangle_cells(top, left, height, width):
        return {
            row * _grid_size + column
            for row in range(top, top + height)
            for column in range(left, left + width)
        }

    _target_blocks = []
    for _target_number in range(_number_of_targets):
        _top = _rng.randrange(_grid_size - _target_height + 1)
        _left = _rng.randrange(_grid_size - _target_width + 1)
        _target_blocks.append(
            {
                "number": _target_number + 1,
                "top": _top,
                "left": _left,
                "height": _target_height,
                "width": _target_width,
                "cells": _rectangle_cells(
                    _top,
                    _left,
                    _target_height,
                    _target_width,
                ),
            }
        )

    _context_top = _rng.randrange(_grid_size - _context_height + 1)
    _context_left = _rng.randrange(_grid_size - _context_width + 1)
    _raw_context = _rectangle_cells(
        _context_top,
        _context_left,
        _context_height,
        _context_width,
    )

    _multiplicity = {
        index: sum(index in block["cells"] for block in _target_blocks)
        for index in range(_grid_size * _grid_size)
    }
    _target_union = {
        index for index, count in _multiplicity.items() if count > 0
    }
    _overlap_cells = {
        index for index, count in _multiplicity.items() if count > 1
    }
    _removed_from_context = _raw_context & _target_union
    _context_cells = _raw_context - _target_union
    _unused_cells = (
        set(range(_grid_size * _grid_size))
        - _context_cells
        - _target_union
    )
    _target_instances = sum(
        len(block["cells"]) for block in _target_blocks
    )

    mask_sample = {
        "grid_size": _grid_size,
        "target_area_fraction": target_area_fraction.value,
        "target_aspect_ratio": target_aspect_ratio.value,
        "target_budget": _target_budget,
        "target_height": _target_height,
        "target_width": _target_width,
        "target_blocks": _target_blocks,
        "target_union": _target_union,
        "target_instances": _target_instances,
        "duplicate_memberships": _target_instances - len(_target_union),
        "overlap_cells": _overlap_cells,
        "context_area_fraction": context_area_fraction.value,
        "context_budget": _context_budget,
        "context_top": _context_top,
        "context_left": _context_left,
        "context_height": _context_height,
        "context_width": _context_width,
        "raw_context": _raw_context,
        "removed_from_context": _removed_from_context,
        "context_cells": _context_cells,
        "unused_cells": _unused_cells,
    }
    return (mask_sample,)


@app.cell(hide_code=True)
def _(
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    crop,
    context_area_fraction,
    image_src,
    mask_sample,
    mo,
    sample_masks,
    target_area_fraction,
    target_aspect_ratio,
):
    _patch_size = 14
    _grid_size = mask_sample["grid_size"]
    _output_size = _patch_size * _grid_size

    def _cell_rectangles(indices, class_name):
        return "".join(
            f'<rect x="{(index % _grid_size) * _patch_size}" '
            f'y="{(index // _grid_size) * _patch_size}" '
            f'width="{_patch_size}" height="{_patch_size}" '
            f'class="{class_name}"></rect>'
            for index in sorted(indices)
        )

    _vertical_lines = " ".join(
        f"M {column * _patch_size} 0 V {_output_size}"
        for column in range(1, _grid_size)
    )
    _horizontal_lines = " ".join(
        f"M 0 {row * _patch_size} H {_output_size}"
        for row in range(1, _grid_size)
    )
    _grid_path = f"{_vertical_lines} {_horizontal_lines}"

    if crop["valid"]:
        _target_single_cells = (
            mask_sample["target_union"] - mask_sample["overlap_cells"]
        )
        _target_fills = _cell_rectangles(
            _target_single_cells,
            "ij-mask-target-cell",
        )
        _target_overlap_fills = _cell_rectangles(
            mask_sample["overlap_cells"],
            "ij-mask-overlap-cell",
        )
        _target_outlines = "".join(
            f'''
              <rect
                x="{block['left'] * _patch_size}"
                y="{block['top'] * _patch_size}"
                width="{block['width'] * _patch_size}"
                height="{block['height'] * _patch_size}"
                class="ij-mask-target-outline"
              ></rect>
              <text
                x="{block['left'] * _patch_size + 4}"
                y="{block['top'] * _patch_size + 11}"
                class="ij-mask-target-label"
              >T{block['number']}</text>
            '''
            for block in mask_sample["target_blocks"]
        )

        _context_fills = _cell_rectangles(
            mask_sample["context_cells"],
            "ij-mask-context-cell",
        )
        _context_target_fills = _cell_rectangles(
            mask_sample["target_union"],
            "ij-mask-target-cell",
        )
        _unused_fills = _cell_rectangles(
            mask_sample["unused_cells"],
            "ij-mask-unused-cell",
        )
        _context_outline_x = mask_sample["context_left"] * _patch_size
        _context_outline_y = mask_sample["context_top"] * _patch_size
        _context_outline_width = (
            mask_sample["context_width"] * _patch_size
        )
        _context_outline_height = (
            mask_sample["context_height"] * _patch_size
        )

        _mask_content = f"""
          <svg class="ij-mask-image-defs" aria-hidden="true">
            <defs>
              <image id="ij-mask-cat-source" href="{image_src}" width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}"></image>
            </defs>
          </svg>

          <div class="ij-mask-stage">
            <div class="ij-mask-panel">
              <div class="ij-mask-panel-label">1 &middot; four target blocks</div>
              <svg
                class="ij-mask-grid"
                viewBox="0 0 {_output_size} {_output_size}"
                role="img"
                aria-label="Four target blocks on the sixteen by sixteen patch grid. They contain {len(mask_sample['target_union'])} unique target positions, including {len(mask_sample['overlap_cells'])} positions covered by more than one block."
              >
                <defs>
                  <pattern id="ij-mask-overlap-pattern" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                    <rect width="6" height="6" class="ij-mask-overlap-base"></rect>
                    <line x1="0" y1="0" x2="0" y2="6" class="ij-mask-overlap-line"></line>
                  </pattern>
                </defs>
                <svg
                  width="{_output_size}"
                  height="{_output_size}"
                  viewBox="{crop['left']} {crop['top']} {crop['width']} {crop['height']}"
                  preserveAspectRatio="none"
                >
                  <use href="#ij-mask-cat-source"></use>
                </svg>
                {_target_fills}
                {_target_overlap_fills}
                <path d="{_grid_path}" class="ij-mask-grid-shadow"></path>
                <path d="{_grid_path}" class="ij-mask-grid-lines"></path>
                {_target_outlines}
                <rect x="0" y="0" width="{_output_size}" height="{_output_size}" class="ij-mask-grid-border"></rect>
              </svg>
              <div class="ij-mask-summary">
                4 × {mask_sample['target_height']} × {mask_sample['target_width']} = {mask_sample['target_instances']} target instances<br>
                {len(mask_sample['target_union'])} unique positions &middot; {mask_sample['duplicate_memberships']} duplicate memberships
              </div>
            </div>

            <div class="ij-mask-transition" aria-label="Sample a context block and remove every target position from it">
              <span>sample context</span>
              <span>remove targets</span>
              <span class="ij-mask-arrow ij-mask-arrow-right" aria-hidden="true">→</span>
              <span class="ij-mask-arrow ij-mask-arrow-down" aria-hidden="true">↓</span>
            </div>

            <div class="ij-mask-panel">
              <div class="ij-mask-panel-label">2 &middot; retained context</div>
              <svg
                class="ij-mask-grid"
                viewBox="0 0 {_output_size} {_output_size}"
                role="img"
                aria-label="The separately sampled context block after target positions are removed. {len(mask_sample['context_cells'])} positions remain as context, {len(mask_sample['removed_from_context'])} target positions are removed, and {len(mask_sample['unused_cells'])} positions are unused."
              >
                <defs>
                </defs>
                <svg
                  width="{_output_size}"
                  height="{_output_size}"
                  viewBox="{crop['left']} {crop['top']} {crop['width']} {crop['height']}"
                  preserveAspectRatio="none"
                >
                  <use href="#ij-mask-cat-source"></use>
                </svg>
                {_context_fills}
                {_context_target_fills}
                {_unused_fills}
                <rect
                  x="{_context_outline_x}"
                  y="{_context_outline_y}"
                  width="{_context_outline_width}"
                  height="{_context_outline_height}"
                  class="ij-mask-context-outline"
                ></rect>
                <path d="{_grid_path}" class="ij-mask-grid-shadow"></path>
                <path d="{_grid_path}" class="ij-mask-grid-lines"></path>
                <rect x="0" y="0" width="{_output_size}" height="{_output_size}" class="ij-mask-grid-border"></rect>
              </svg>
              <div class="ij-mask-summary">
                {len(mask_sample['raw_context'])} raw context − {len(mask_sample['removed_from_context'])} targets = {len(mask_sample['context_cells'])} retained<br>
                {len(mask_sample['unused_cells'])} positions used by neither branch
              </div>
            </div>
          </div>

          <div class="ij-mask-legend" aria-label="Mask legend">
            <span><i class="ij-mask-swatch ij-mask-swatch-context" aria-hidden="true"></i>retained context</span>
            <span><i class="ij-mask-swatch ij-mask-swatch-target" aria-hidden="true"></i>target</span>
            <span><i class="ij-mask-swatch ij-mask-swatch-overlap" aria-hidden="true"></i>target overlap</span>
            <span><i class="ij-mask-swatch ij-mask-swatch-unused" aria-hidden="true"></i>unused</span>
          </div>

          <div class="ij-mask-geometry">
            target request {mask_sample['target_area_fraction']:.2f} × 256 → {mask_sample['target_height']} × {mask_sample['target_width']} patches
            &nbsp;&middot;&nbsp;
            context request {mask_sample['context_area_fraction']:.2f} × 256 → {mask_sample['context_height']} × {mask_sample['context_width']} patches
          </div>
        """
    else:
        _mask_content = """
          <p class="ij-mask-unavailable">No target or context masks are formed because the current crop geometry would be rejected.</p>
        """

    _mask_visual = mo.Html(
        f"""
        <style>
          #ij-mask-sampler {{
            --ij-mask-muted: #5f6368;
            --ij-mask-border: #272a2e;
            --ij-mask-grid-light: rgb(255 255 255 / 78%);
            --ij-mask-grid-dark: rgb(0 0 0 / 68%);
            --ij-mask-target: #cf4f24;
            --ij-mask-target-fill: rgb(207 79 36 / 34%);
            --ij-mask-overlap-fill: rgb(156 45 31 / 58%);
            --ij-mask-context: #2f6f9f;
            --ij-mask-context-fill: rgb(47 111 159 / 34%);
            --ij-mask-unused-fill: rgb(45 48 52 / 55%);
            --ij-mask-label-halo: #ffffff;
            --ij-mask-rejected: #a33a31;
            box-sizing: border-box;
            margin: 0 auto;
            max-width: 900px;
            padding: 0.75rem;
            width: 100%;
          }}

          #ij-mask-sampler * {{
            box-sizing: border-box;
          }}

          #ij-mask-sampler .ij-mask-image-defs {{
            height: 0;
            overflow: hidden;
            position: absolute;
            width: 0;
          }}

          #ij-mask-sampler .ij-mask-stage {{
            align-items: center;
            display: grid;
            gap: 1rem;
            grid-template-columns: minmax(0, 1fr) 7rem minmax(0, 1fr);
          }}

          #ij-mask-sampler .ij-mask-panel {{
            min-width: 0;
            text-align: center;
          }}

          #ij-mask-sampler .ij-mask-panel-label {{
            color: var(--ij-mask-muted);
            font-size: 0.82rem;
            font-weight: 500;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
          }}

          #ij-mask-sampler .ij-mask-grid {{
            display: block;
            height: auto;
            width: 100%;
          }}

          #ij-mask-sampler .ij-mask-target-cell {{
            fill: var(--ij-mask-target-fill);
          }}

          #ij-mask-sampler .ij-mask-overlap-cell {{
            fill: url(#ij-mask-overlap-pattern);
          }}

          #ij-mask-sampler .ij-mask-overlap-base {{
            fill: var(--ij-mask-overlap-fill);
          }}

          #ij-mask-sampler .ij-mask-overlap-line {{
            stroke: var(--ij-mask-label-halo);
            stroke-width: 2;
          }}

          #ij-mask-sampler .ij-mask-target-outline {{
            fill: none;
            stroke: var(--ij-mask-target);
            stroke-width: 2.5;
            vector-effect: non-scaling-stroke;
          }}

          #ij-mask-sampler .ij-mask-target-label {{
            fill: var(--ij-mask-target);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 9px;
            font-weight: 500;
            paint-order: stroke;
            stroke: var(--ij-mask-label-halo);
            stroke-linejoin: round;
            stroke-width: 2.5px;
          }}

          #ij-mask-sampler .ij-mask-context-cell {{
            fill: var(--ij-mask-context-fill);
          }}

          #ij-mask-sampler .ij-mask-unused-cell {{
            fill: var(--ij-mask-unused-fill);
          }}

          #ij-mask-sampler .ij-mask-context-outline {{
            fill: none;
            stroke: var(--ij-mask-context);
            stroke-width: 3;
            vector-effect: non-scaling-stroke;
          }}

          #ij-mask-sampler .ij-mask-grid-shadow {{
            fill: none;
            stroke: var(--ij-mask-grid-dark);
            stroke-width: 1.45;
            vector-effect: non-scaling-stroke;
          }}

          #ij-mask-sampler .ij-mask-grid-lines {{
            fill: none;
            stroke: var(--ij-mask-grid-light);
            stroke-width: 0.62;
            vector-effect: non-scaling-stroke;
          }}

          #ij-mask-sampler .ij-mask-grid-border {{
            fill: none;
            stroke: var(--ij-mask-border);
            stroke-width: 1.5;
            vector-effect: non-scaling-stroke;
          }}

          #ij-mask-sampler .ij-mask-summary,
          #ij-mask-sampler .ij-mask-geometry {{
            color: var(--ij-mask-muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.8rem;
            line-height: 1.55;
          }}

          #ij-mask-sampler .ij-mask-summary {{
            margin-top: 0.5rem;
          }}

          #ij-mask-sampler .ij-mask-transition {{
            align-items: center;
            color: var(--ij-mask-muted);
            display: flex;
            flex-direction: column;
            font-size: 0.78rem;
            font-weight: 500;
            gap: 0.1rem;
            justify-content: center;
            text-align: center;
          }}

          #ij-mask-sampler .ij-mask-arrow {{
            color: var(--ij-mask-context);
            font-size: 2rem;
            line-height: 1;
          }}

          #ij-mask-sampler .ij-mask-arrow-down {{
            display: none;
          }}

          #ij-mask-sampler .ij-mask-legend {{
            color: var(--ij-mask-muted);
            display: flex;
            flex-wrap: wrap;
            font-size: 0.8rem;
            gap: 0.7rem 1rem;
            justify-content: center;
            margin-top: 0.8rem;
          }}

          #ij-mask-sampler .ij-mask-legend span {{
            align-items: center;
            display: inline-flex;
            gap: 0.35rem;
          }}

          #ij-mask-sampler .ij-mask-swatch {{
            border: 1px solid var(--ij-mask-border);
            display: inline-block;
            height: 0.85rem;
            width: 0.85rem;
          }}

          #ij-mask-sampler .ij-mask-swatch-context {{
            background: var(--ij-mask-context-fill);
            border-color: var(--ij-mask-context);
          }}

          #ij-mask-sampler .ij-mask-swatch-target {{
            background: var(--ij-mask-target-fill);
            border-color: var(--ij-mask-target);
          }}

          #ij-mask-sampler .ij-mask-swatch-overlap {{
            background: repeating-linear-gradient(
              45deg,
              var(--ij-mask-overlap-fill) 0 3px,
              var(--ij-mask-label-halo) 3px 4px
            );
          }}

          #ij-mask-sampler .ij-mask-swatch-unused {{
            background: var(--ij-mask-unused-fill);
          }}

          #ij-mask-sampler .ij-mask-geometry {{
            margin-top: 0.55rem;
            text-align: center;
          }}

          #ij-mask-sampler .ij-mask-unavailable {{
            color: var(--ij-mask-rejected);
            margin: 0;
            text-align: center;
          }}

          @media (max-width: 680px) {{
            #ij-mask-sampler .ij-mask-stage {{
              grid-template-columns: minmax(0, 1fr);
              justify-items: center;
            }}

            #ij-mask-sampler .ij-mask-panel {{
              max-width: 420px;
              width: 100%;
            }}

            #ij-mask-sampler .ij-mask-transition {{
              min-height: 3.4rem;
            }}

            #ij-mask-sampler .ij-mask-arrow-right {{
              display: none;
            }}

            #ij-mask-sampler .ij-mask-arrow-down {{
              display: inline;
            }}
          }}

          @media (max-width: 420px) {{
            #ij-mask-sampler {{
              padding: 0.4rem;
            }}

            #ij-mask-sampler .ij-mask-summary,
            #ij-mask-sampler .ij-mask-geometry,
            #ij-mask-sampler .ij-mask-legend,
            #ij-mask-sampler .ij-mask-transition {{
              font-size: 0.72rem;
            }}
          }}

          @media (prefers-color-scheme: dark) {{
            #ij-mask-sampler {{
              --ij-mask-muted: #b8bdc3;
              --ij-mask-border: #e1e4e8;
              --ij-mask-grid-light: rgb(255 255 255 / 62%);
              --ij-mask-grid-dark: rgb(0 0 0 / 78%);
              --ij-mask-target: #ff9a68;
              --ij-mask-target-fill: rgb(255 154 104 / 34%);
              --ij-mask-overlap-fill: rgb(255 118 91 / 58%);
              --ij-mask-context: #9bc3ec;
              --ij-mask-context-fill: rgb(92 160 219 / 38%);
              --ij-mask-unused-fill: rgb(15 17 20 / 64%);
              --ij-mask-label-halo: #17191c;
              --ij-mask-rejected: #ff9990;
            }}
          }}
        </style>

        <section id="ij-mask-sampler" aria-label="Sample I-JEPA target blocks and a non-overlapping context region">
          {_mask_content}
        </section>
        """
    )

    _mask_controls = mo.vstack(
        [
            mo.hstack(
                [target_area_fraction, target_aspect_ratio],
                widths="equal",
                wrap=True,
                align="end",
                gap=0.8,
            ),
            mo.hstack(
                [context_area_fraction, sample_masks],
                widths="equal",
                wrap=True,
                align="end",
                gap=0.8,
            ),
        ],
        gap=0.55,
    )
    mo.vstack([_mask_controls, _mask_visual], gap=0.8).style(
        {"max-width": "900px", "margin": "0 auto", "padding": "0.5rem"}
    )
    return


if __name__ == "__main__":
    app.run()

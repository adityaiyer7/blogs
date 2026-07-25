# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.23.14",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="V-JEPA sampled clip")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.Html(
        """
        <style>
          #vj-sampled-clip {
            --vj-ink: #202124;
            --vj-muted: #4f5358;
            box-sizing: border-box;
            color: var(--vj-ink);
            margin: 0 auto;
            max-width: 980px;
            padding: 0.5rem;
            width: 100%;
          }

          #vj-sampled-clip * {
            box-sizing: border-box;
          }

          #vj-sampled-clip .vj-diagram {
            color: var(--vj-ink);
            display: block;
            height: auto;
            overflow: visible;
            width: 100%;
          }

          #vj-sampled-clip .vj-mobile-diagram {
            display: none;
          }

          #vj-sampled-clip .vj-formula,
          #vj-sampled-clip .vj-frame-label,
          #vj-sampled-clip .vj-dimension,
          #vj-sampled-clip .vj-time-label,
          #vj-sampled-clip .vj-duration {
            fill: currentColor;
            font-family: Georgia, Cambria, "Times New Roman", serif;
          }

          #vj-sampled-clip .vj-formula {
            font-size: 34px;
          }

          #vj-sampled-clip .vj-formula-symbol,
          #vj-sampled-clip .vj-frame-symbol {
            font-style: italic;
          }

          #vj-sampled-clip .vj-formula-subscript {
            font-size: 18px;
          }

          #vj-sampled-clip .vj-frame {
            fill: none;
            stroke: currentColor;
            stroke-linejoin: round;
            stroke-width: 2.6;
            vector-effect: non-scaling-stroke;
          }

          #vj-sampled-clip .vj-frame-label {
            font-size: 30px;
          }

          #vj-sampled-clip .vj-frame-subscript {
            font-size: 18px;
          }

          #vj-sampled-clip .vj-ellipsis {
            fill: currentColor;
          }

          #vj-sampled-clip .vj-axis,
          #vj-sampled-clip .vj-dimension-line,
          #vj-sampled-clip .vj-bracket {
            fill: none;
            stroke: currentColor;
            stroke-linecap: round;
            stroke-linejoin: round;
            stroke-width: 1.9;
            vector-effect: non-scaling-stroke;
          }

          #vj-sampled-clip .vj-marker {
            fill: currentColor;
          }

          #vj-sampled-clip .vj-dimension {
            font-size: 24px;
          }

          #vj-sampled-clip .vj-time-label {
            font-size: 27px;
          }

          #vj-sampled-clip .vj-duration {
            font-size: 29px;
          }

          @media (max-width: 560px) {
            #vj-sampled-clip {
              padding: 0.25rem;
            }

            #vj-sampled-clip .vj-desktop-diagram {
              display: none;
            }

            #vj-sampled-clip .vj-mobile-diagram {
              display: block;
            }
          }

          @media (prefers-color-scheme: dark) {
            #vj-sampled-clip {
              --vj-ink: #e1e4e8;
              --vj-muted: #b8bdc3;
            }
          }
        </style>

        <figure
          id="vj-sampled-clip"
          aria-label="A four-second V-JEPA sample containing sixteen 256 by 256 frames sampled at four frames per second."
        >
          <svg
            class="vj-diagram vj-desktop-diagram"
            viewBox="0 0 1200 630"
            role="img"
            aria-labelledby="vj-sampled-title vj-sampled-desc"
          >
            <title id="vj-sampled-title">Sixteen-frame V-JEPA sample</title>
            <desc id="vj-sampled-desc">
              A sequence diagram showing the first three sampled frames, an
              ellipsis, and the sixteenth sampled frame. The sample lasts four
              seconds, is sampled at four frames per second, and each frame is
              256 pixels high and wide.
            </desc>

            <defs>
              <marker
                id="vj-arrow-end"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 Z" class="vj-marker"></path>
              </marker>
            </defs>

            <text x="130" y="57" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">T</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = 4 s</tspan>
            </text>
            <text x="482" y="57" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">f</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = 4 fps</tspan>
            </text>
            <text x="895" y="57" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">N</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = </tspan>
              <tspan class="vj-formula-symbol">T</tspan>
              <tspan class="vj-formula-symbol">f</tspan>
              <tspan> = 16 frames</tspan>
            </text>

            <path d="M 50 105 L 178 158 L 178 367 L 50 314 Z" class="vj-frame"></path>
            <path d="M 262 105 L 390 158 L 390 367 L 262 314 Z" class="vj-frame"></path>
            <path d="M 474 105 L 602 158 L 602 367 L 474 314 Z" class="vj-frame"></path>
            <path d="M 922 105 L 1050 158 L 1050 367 L 922 314 Z" class="vj-frame"></path>

            <text x="114" y="414" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">1</tspan>
            </text>
            <text x="326" y="414" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">2</tspan>
            </text>
            <text x="538" y="414" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">3</tspan>
            </text>
            <text x="986" y="414" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">16</tspan>
            </text>

            <circle cx="710" cy="238" r="6" class="vj-ellipsis"></circle>
            <circle cx="770" cy="238" r="6" class="vj-ellipsis"></circle>
            <circle cx="830" cy="238" r="6" class="vj-ellipsis"></circle>

            <line
              x1="1088"
              y1="112"
              x2="1088"
              y2="359"
              marker-start="url(#vj-arrow-end)"
              marker-end="url(#vj-arrow-end)"
              class="vj-dimension-line"
            ></line>
            <text x="1110" y="242" class="vj-dimension">256 px</text>

            <line
              x1="916"
              y1="350"
              x2="1045"
              y2="403"
              marker-start="url(#vj-arrow-end)"
              marker-end="url(#vj-arrow-end)"
              class="vj-dimension-line"
            ></line>
            <text
              x="977"
              y="397"
              text-anchor="middle"
              transform="rotate(22 977 397)"
              class="vj-dimension"
            >256 px</text>

            <line
              x1="34"
              y1="462"
              x2="1164"
              y2="462"
              marker-end="url(#vj-arrow-end)"
              class="vj-axis"
            ></line>
            <text x="599" y="504" text-anchor="middle" class="vj-time-label">time</text>

            <path
              d="M 35 532
                 C 35 542, 42 548, 55 548
                 H 568
                 C 584 548, 592 554, 599 568
                 C 606 554, 614 548, 630 548
                 H 1143
                 C 1156 548, 1163 542, 1163 532"
              class="vj-bracket"
            ></path>
            <text x="599" y="610" text-anchor="middle" class="vj-duration">4 s</text>
          </svg>

          <svg
            class="vj-diagram vj-mobile-diagram"
            viewBox="0 0 640 720"
            role="img"
            aria-labelledby="vj-sampled-mobile-title vj-sampled-mobile-desc"
          >
            <title id="vj-sampled-mobile-title">Sixteen-frame V-JEPA sample</title>
            <desc id="vj-sampled-mobile-desc">
              A compact sequence diagram showing the first two sampled frames,
              an ellipsis, and the sixteenth sampled frame. The sample lasts
              four seconds, is sampled at four frames per second, and each
              frame is 256 pixels high and wide.
            </desc>

            <defs>
              <marker
                id="vj-mobile-arrow-end"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 Z" class="vj-marker"></path>
              </marker>
            </defs>

            <text x="170" y="45" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">T</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = 4 s</tspan>
            </text>
            <text x="470" y="45" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">f</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = 4 fps</tspan>
            </text>
            <text x="320" y="92" text-anchor="middle" class="vj-formula">
              <tspan class="vj-formula-symbol">N</tspan>
              <tspan baseline-shift="sub" class="vj-formula-subscript">sample</tspan>
              <tspan baseline-shift="baseline"> = </tspan>
              <tspan class="vj-formula-symbol">T</tspan>
              <tspan class="vj-formula-symbol">f</tspan>
              <tspan> = 16 frames</tspan>
            </text>

            <path d="M 32 140 L 130 180 L 130 382 L 32 342 Z" class="vj-frame"></path>
            <path d="M 190 140 L 288 180 L 288 382 L 190 342 Z" class="vj-frame"></path>
            <path d="M 466 140 L 564 180 L 564 382 L 466 342 Z" class="vj-frame"></path>

            <text x="81" y="428" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">1</tspan>
            </text>
            <text x="239" y="428" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">2</tspan>
            </text>
            <text x="515" y="428" text-anchor="middle" class="vj-frame-label">
              <tspan class="vj-frame-symbol">s</tspan>
              <tspan baseline-shift="sub" class="vj-frame-subscript">16</tspan>
            </text>

            <circle cx="346" cy="255" r="5" class="vj-ellipsis"></circle>
            <circle cx="382" cy="255" r="5" class="vj-ellipsis"></circle>
            <circle cx="418" cy="255" r="5" class="vj-ellipsis"></circle>

            <line
              x1="592"
              y1="147"
              x2="592"
              y2="375"
              marker-start="url(#vj-mobile-arrow-end)"
              marker-end="url(#vj-mobile-arrow-end)"
              class="vj-dimension-line"
            ></line>
            <text x="610" y="268" class="vj-dimension">256 px</text>

            <line
              x1="460"
              y1="369"
              x2="558"
              y2="409"
              marker-start="url(#vj-mobile-arrow-end)"
              marker-end="url(#vj-mobile-arrow-end)"
              class="vj-dimension-line"
            ></line>
            <text
              x="505"
              y="412"
              text-anchor="middle"
              transform="rotate(22 505 412)"
              class="vj-dimension"
            >256 px</text>

            <line
              x1="20"
              y1="482"
              x2="620"
              y2="482"
              marker-end="url(#vj-mobile-arrow-end)"
              class="vj-axis"
            ></line>
            <text x="320" y="524" text-anchor="middle" class="vj-time-label">time</text>

            <path
              d="M 22 562
                 C 22 572, 30 578, 42 578
                 H 288
                 C 304 578, 313 584, 320 598
                 C 327 584, 336 578, 352 578
                 H 598
                 C 610 578, 618 572, 618 562"
              class="vj-bracket"
            ></path>
            <text x="320" y="650" text-anchor="middle" class="vj-duration">4 s</text>
          </svg>
        </figure>
        """
    )
    return


if __name__ == "__main__":
    app.run()

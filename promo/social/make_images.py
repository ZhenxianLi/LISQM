#!/usr/bin/env python3
"""Images for posts about LISQM on LinkedIn and elsewhere (not used by the website).

Writes an SVG and a PNG (at twice the size) for each variant into this folder. The PNGs are rendered with
headless Chromium and cropped with ImageMagick:

    python3 promo/social/make_images.py [path-to-chromium]

The final images are lisqm-square (the one posted) and lisqm-landscape; the alt-* files are earlier options kept
for reference.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

FONT = "Charter, 'Bitstream Charter', Georgia, 'Liberation Serif', 'DejaVu Serif', serif"
TITLE = ("A List of Open-Source Implementations of", "Psychoacoustic and Sound Quality Metrics")
TITLE_3 = ("A List of Open-Source", "Implementations of Psychoacoustic", "and Sound Quality Metrics")
DESCRIPTION = ("Each listed under the standard edition it follows · with its validation, licence and activity · "
               "renewed monthly")
QUESTION = ("Are you looking for an open-source way", "to calculate psychoacoustic metrics?")
METRICS = "Loudness · Sharpness · Roughness · Fluctuation strength · Tonality · Impulsiveness · Annoyance"
URL = "zhenxianli.github.io/LISQM"
LANGUAGES = [("PYTHON", "#2463ad"), ("MATLAB / OCTAVE", "#bd5512"), ("C / C++", "#6b46a6"), ("RUST", "#94471c"),
             ("JULIA", "#8b3aa9"), ("PURE DATA", "#36606e")]

# The website's mark: an ear and three level bars, in white on green (site-src/favicon.svg).
MARK = """<g transform="translate({x} {y}) scale({s})">
    <rect width="64" height="64" rx="14" fill="#25c59b"/>
    <g fill="none" stroke="#fff" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M26 31C26 19 33 11 42 11C51 11 56 18 56 27C56 35 50 39 47 44C44 49 45 55 38 56C34 57 31 54 31 51"/>
      <path d="M34 30C34 24 37 20 42 20C46.5 20 48 24.5 46 28.5C44.5 31.5 41 32.5 41 37"/>
    </g>
    <g fill="#fff"><rect x="8" y="46" width="4" height="10" rx="2"/><rect x="14.5" y="40" width="4" height="16" rx="2"/><rect x="21" y="34" width="4" height="22" rx="2"/></g>
  </g>"""


def lines(texts, y0, step, size, extra=""):
    spans = "".join(f'<tspan x="100" y="{y0 + i * step}">{t}</tspan>' for i, t in enumerate(texts))
    return f'<text font-size="{size}" {extra}>{spans}</text>'


def text(content, y, size, extra=""):
    return f'<text x="100" y="{y}" font-size="{size}" {extra}>{content}</text>'


def languages(y, size):
    dot = '<tspan fill="#8b949e">  ·  </tspan>'
    spans = dot.join(f'<tspan fill="{c}">{n}</tspan>' for n, c in LANGUAGES)
    return text(spans, y, size, 'font-weight="700" letter-spacing="1.5"')


def page(w, h, mark, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" fill="#ffffff"/>
  <rect width="{w}" height="52" fill="#25c59b"/><rect y="52" width="{w}" height="9" fill="#0f7d60"/>
  {MARK.format(**mark)}
  <g font-family="{FONT}" fill="#1f2328">
    {body}
    <rect x="100" y="{{rule}}" width="{w - 200}" height="1.5" fill="#2b3137"/>
  </g>
</svg>"""


GREY = 'font-style="italic" fill="#5a636e"'
GREEN_BOLD = 'font-weight="700" fill="#0f7d60"'

VARIANTS = {
    # Final square, as posted: the question, LISQM as the title, the full name as the green subtitle.
    "lisqm-square": (1200, 1200, dict(x=100, y=150, s=1.8), 818, "\n    ".join([
        lines(QUESTION, 380, 50, 38, GREY),
        text("LISQM", 590, 110, 'font-weight="700" letter-spacing="-2"'),
        lines(TITLE, 656, 48, 38, GREEN_BOLD),
        text(DESCRIPTION, 768, 23, GREY),
        text(METRICS, 880, 25),
        languages(940, 25),
        text(URL, 1090, 32, GREEN_BOLD)])),
    # Final landscape (1.91:1): the full name as the title on two lines, LISQM under it.
    "lisqm-landscape": (1200, 627, dict(x=1012, y=100, s=1.4), 432, "\n    ".join([
        lines(TITLE, 200, 62, 48, 'font-weight="700" letter-spacing="-0.3"'),
        text("LISQM", 348, 38, 'font-weight="700" letter-spacing="3" fill="#0f7d60"'),
        text(DESCRIPTION, 392, 21, GREY),
        text(METRICS, 482, 21),
        languages(532, 21)])),
    # Earlier option: the landscape image with the full name on three lines.
    "alt-landscape-three-line-title": (1200, 627, dict(x=1012, y=100, s=1.4), 462, "\n    ".join([
        lines(TITLE_3, 160, 70, 58, 'font-weight="700" letter-spacing="-0.5"'),
        text("LISQM", 384, 46, 'font-weight="700" letter-spacing="3" fill="#0f7d60"'),
        text(DESCRIPTION, 424, 21, GREY),
        text(METRICS, 508, 21),
        languages(556, 21)])),
    # Earlier option: square, the full name as the title, no question.
    "alt-square-title-first": (1200, 1200, dict(x=100, y=170, s=1.8), 720, "\n    ".join([
        lines(TITLE, 440, 64, 48, 'font-weight="700" letter-spacing="-0.3"'),
        text("LISQM", 600, 38, 'font-weight="700" letter-spacing="3" fill="#0f7d60"'),
        text(DESCRIPTION, 648, 21, GREY),
        text(METRICS, 784, 21),
        languages(846, 21),
        text(URL, 1090, 28, GREEN_BOLD)])),
    # Earlier option: the final square with a larger LISQM and smaller text.
    "alt-square-large-lisqm": (1200, 1200, dict(x=100, y=150, s=1.8), 830, "\n    ".join([
        lines(QUESTION, 370, 46, 34, GREY),
        text("LISQM", 610, 150, 'font-weight="700" letter-spacing="-2"'),
        lines(TITLE, 680, 44, 34, GREEN_BOLD),
        text(DESCRIPTION, 776, 21, GREY),
        text(METRICS, 885, 21),
        languages(940, 21),
        text(URL, 1090, 28, GREEN_BOLD)])),
}


def render(name, w, h, svg):
    path = HERE / f"{name}.svg"
    path.write_text(svg + "\n", encoding="utf-8")
    raw = HERE / "raw.png"
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size={w},{h + 300}", f"--screenshot={raw}",
                    path.as_uri()], capture_output=True, check=True)
    subprocess.run(["convert", str(raw), "-crop", f"{2 * w}x{2 * h}+0+0", "+repage", str(HERE / f"{name}.png")],
                   check=True)
    raw.unlink()


if __name__ == "__main__":
    if not shutil.which("convert"):
        sys.exit("ImageMagick (convert) is needed to crop the screenshots.")
    for name, (w, h, mark, rule, body) in VARIANTS.items():
        render(name, w, h, page(w, h, mark, body).replace("{rule}", str(rule)))
        print(f"wrote {name}.svg and {name}.png")

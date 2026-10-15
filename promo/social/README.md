# Images for posts about LISQM

Images made for posts about LISQM on LinkedIn and other platforms, kept here as a backup. The website does not
use them; its own preview image is `assets/social-preview.png`.

| File | Size (px) | Use |
|---|---|---|
| `lisqm-square.png` | 2400 × 2400 | Final square image, as posted on LinkedIn |
| `lisqm-landscape.png` | 2400 × 1254 | Final landscape image (1.91:1, LinkedIn's link format) |
| `alt-square-large-lisqm.png` | 2400 × 2400 | Earlier option: the square with a larger LISQM and smaller text |
| `alt-square-title-first.png` | 2400 × 2400 | Earlier option: the square with the full name as the title, no question |
| `alt-landscape-three-line-title.png` | 2400 × 1254 | Earlier option: the landscape with the full name on three lines |

Each PNG has an SVG next to it. `make_images.py` writes them all again, for example after a change of wording:

```sh
python3 promo/social/make_images.py              # Chromium at the default path of a Claude Code cloud session
python3 promo/social/make_images.py /path/to/chrome
```

It needs headless Chromium (or Chrome) and ImageMagick. The text is set in Charter where it is installed, and
in Liberation Serif or DejaVu Serif otherwise, as in the PNGs here.

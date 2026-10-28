#!/usr/bin/env python3
"""Convert an image to ASCII art.

Usage:
    python draw.py path/to/image.jpg
    python draw.py path/to/image.png --charset braille --width 120
    python draw.py path/to/image.jpg --width 150 --charset detailed --invert

The result is written to ``ascii_art.txt`` in the project root (the folder
containing this script), regardless of where you run the command from.

Paths that contain spaces must be wrapped in quotes.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / "ascii_art.txt"

# Character ramps, ordered from darkest (most ink) to lightest (least ink).
RAMPS = {
    "simple": "@%#*+=-:. ",
    "standard": r"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    # All 95 printable ASCII characters, ranked by measured ink density
    # (DejaVu Sans Mono), so every step is a genuinely different shade.
    "detailed": "MBNW@8Q#R0DgOH9&6KUqGpdbEA$mPSa5X4Ze3hkV2wo%FIyCnuJ{T1}Ysftj7xLz[]ivcl?=|<>)(+\\/r*!_^;\"~:,'-.` ",
    "blocks": "█▓▒░ ",
}
BRAILLE = "braille"
BRAILLE_MAX = "braille_max"  # braille + more characters + sharpening
CHARSET_NAMES = [*RAMPS, BRAILLE, BRAILLE_MAX]

# Default output width in characters when --width is not given.
DEFAULT_WIDTH = 220
DEFAULT_WIDTHS = {BRAILLE_MAX: 300}

# Terminal characters are roughly twice as tall as they are wide,
# so the height is squashed to keep the picture's proportions.
CHAR_ASPECT = 0.55

# Each braille character is a 2x4 grid of dots; these are the bit values
# for the dot at (column, row) inside the cell.
BRAILLE_BITS = ((0x01, 0x02, 0x04, 0x40), (0x08, 0x10, 0x20, 0x80))
BRAILLE_BASE = 0x2800


def load_image(path: Path) -> Image.Image:
    """Open an image, flatten transparency onto white, return grayscale."""
    image = Image.open(path)
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    gray = image.convert("L")
    # Stretch the tonal range so flat or washed-out images still use the full ramp.
    return ImageOps.autocontrast(gray, cutoff=1)


def resize_image(image: Image.Image, new_width: int, aspect: float, height_multiple: int = 1) -> Image.Image:
    width, height = image.size
    new_height = max(height_multiple, int(new_width * (height / width) * aspect))
    new_height -= new_height % height_multiple or 0
    new_height = max(height_multiple, new_height)
    return image.resize((new_width, new_height), Image.LANCZOS)


def ramp_to_ascii(image: Image.Image, chars: str) -> str:
    """Map each grayscale pixel (0-255) to a character and join into lines."""
    scale = len(chars) / 256
    symbols = [chars[int(pixel * scale)] for pixel in image.tobytes()]
    width = image.width
    rows = ("".join(symbols[i:i + width]) for i in range(0, len(symbols), width))
    return "\n".join(rows)


def braille_art(image: Image.Image, invert: bool) -> str:
    """Render a grayscale image as braille: 2x4 dithered pixels per character."""
    # Floyd-Steinberg dithering turns gray tones into dot density.
    bw = image.convert("1")  # 0 = black, 255 = white
    width, height = bw.size
    pixels = bw.load()
    lines = []
    for y in range(0, height, 4):
        line = []
        for x in range(0, width, 2):
            bits = 0
            for dx in range(2):
                for dy in range(4):
                    on = pixels[x + dx, y + dy] == 0  # dark pixel -> dot
                    if on != invert:
                        bits |= BRAILLE_BITS[dx][dy]
            line.append(chr(BRAILLE_BASE + bits))
        lines.append("".join(line))
    return "\n".join(lines)


def convert(path: Path, width: int, charset: str, invert: bool) -> str:
    gray = load_image(path)
    if charset in (BRAILLE, BRAILLE_MAX):
        # 2 pixels per character horizontally, 4 vertically: dots are square,
        # so no aspect correction is needed. Height must be a multiple of 4.
        pixel_width = width * 2
        gray = resize_image(gray, pixel_width, aspect=1.0, height_multiple=4)
        if charset == BRAILLE_MAX:
            # Downscaling softens edges; sharpen so fine detail survives dithering.
            gray = gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=160, threshold=2))
        return braille_art(gray, invert)

    chars = RAMPS[charset]
    if invert:
        chars = chars[::-1]
    gray = resize_image(gray, width, aspect=CHAR_ASPECT)
    return ramp_to_ascii(gray, chars)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    parser.add_argument("image", type=Path, help="path to the input image (quote it if it has spaces)")
    parser.add_argument("-w", "--width", type=int, default=None,
                        help=f"output width in characters (default: {DEFAULT_WIDTH}, "
                             f"{DEFAULT_WIDTHS[BRAILLE_MAX]} for braille_max)")
    parser.add_argument("-c", "--charset", choices=CHARSET_NAMES, default="standard",
                        help="character set; 'braille_max' gives the highest detail (default: standard)")
    parser.add_argument("-i", "--invert", action="store_true",
                        help="invert brightness (use for light text on a dark background)")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT,
                        help="output file (default: ascii_art.txt in the project root)")
    parser.add_argument("-p", "--print", dest="show", action="store_true",
                        help="also print the result to the terminal")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.width is None:
        args.width = DEFAULT_WIDTHS.get(args.charset, DEFAULT_WIDTH)

    if args.width < 1:
        print("Error: --width must be at least 1.", file=sys.stderr)
        return 1

    try:
        art = convert(args.image, args.width, args.charset, args.invert)
    except FileNotFoundError:
        print(f"Error: file not found: {args.image}", file=sys.stderr)
        return 1
    except UnidentifiedImageError:
        print(f"Error: {args.image} is not a valid image file.", file=sys.stderr)
        return 1

    args.output.write_text(art + "\n", encoding="utf-8")
    print(f"Saved ASCII art to {args.output}")

    if args.show:
        print(art)
    return 0


if __name__ == "__main__":
    sys.exit(main())
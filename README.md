# ASCII Art Converter

Turn any image into ASCII art with a single command.

## Quick start

```bash
git clone https://github.com/Henrycoding-design/ascii_drawer.git
cd ascii_drawer
pip install -r requirements.txt

python drawer.py path/to/your/image.jpg
```

The result is saved to **`ascii_art.txt`** in the project root. Open it with a
monospaced font (and zoom out if the image is wide).

## Options

| Option | Description | Default |
| --- | --- | --- |
| `-w`, `--width` | Output width in characters | `220` |
| `-c`, `--charset` | `simple`, `standard` or `blocks` | `standard` |
| `-i`, `--invert` | Flip brightness (for light text on a dark background) | off |
| `-o`, `--output` | Output file | `ascii_art.txt` |
| `-p`, `--print` | Also print the result to the terminal | off |

Examples:

```bash
python drawer.py photo.png --width 120
python drawer.py photo.png -c blocks -i -p
python drawer.py "C:\Users\me\My Pictures\cat.jpg" # quote paths with spaces
```

## How it works

1. Open the image and flatten transparency onto a white background.
2. Convert to grayscale and resize (height is squashed because characters are taller than wide).
3. Map each pixel's brightness to a character, from dense (dark) to sparse (light).
4. Write the rows to a text file.

## Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/pillow/)

## License

[MIT](LICENSE)
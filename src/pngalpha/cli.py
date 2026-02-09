"""
Two-pass alpha extraction CLI tool.
"""

from __future__ import annotations

import sys

from pngalpha.core import extract_alpha_two_pass


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 4:
        print("Usage: pngalpha <image_on_white> <image_on_black> <output_file>")
        print()
        print("Creates a transparent PNG file from two images:")
        print("one on a white background and one on a black background.")
        print()
        print("Example: pngalpha image_white.png image_black.png output.png")
        return 1

    img_on_white_path = sys.argv[1]
    img_on_black_path = sys.argv[2]
    output_path = sys.argv[3]

    try:
        extract_alpha_two_pass(img_on_white_path, img_on_black_path, output_path)
        print(f"Transparent PNG file created: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

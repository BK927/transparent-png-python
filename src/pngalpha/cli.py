"""
Two-pass alpha extraction CLI tool.

Takes two images of the same subject - one on white background, one on black background.
Calculates the alpha channel and recovers the original foreground color.
"""

import sys
import numpy as np
from PIL import Image


def extract_alpha_two_pass(
    img_on_white_path: str,
    img_on_black_path: str,
    output_path: str,
) -> None:
    """
    Two-pass alpha extraction algorithm.
    
    Args:
        img_on_white_path: Path to image captured on white background
        img_on_black_path: Path to image captured on black background
        output_path: Path for output transparent PNG file
    """
    # Load images as RGB arrays
    img_white = np.array(Image.open(img_on_white_path).convert("RGB"), dtype=np.float64)
    img_black = np.array(Image.open(img_on_black_path).convert("RGB"), dtype=np.float64)
    
    # Check dimensions match
    if img_white.shape != img_black.shape:
        raise ValueError("Dimension mismatch: Images must be identical size.")
    
    # Distance between White (255,255,255) and Black (0,0,0)
    # sqrt(255^2 + 255^2 + 255^2) ≈ 441.67
    bg_dist = np.sqrt(3.0 * 255 * 255)
    
    # Calculate the distance between the two observed pixels (vectorized)
    pixel_dist = np.sqrt(
        (img_white[:, :, 0] - img_black[:, :, 0]) ** 2 +
        (img_white[:, :, 1] - img_black[:, :, 1]) ** 2 +
        (img_white[:, :, 2] - img_black[:, :, 2]) ** 2
    )
    
    # THE FORMULA:
    # If the pixel is 100% opaque, it looks the same on Black and White (pixelDist = 0).
    # If the pixel is 100% transparent, it looks exactly like the backgrounds (pixelDist = bgDist).
    alpha = 1.0 - (pixel_dist / bg_dist)
    
    # Clamp results to 0-1 range
    alpha = np.clip(alpha, 0.0, 1.0)
    
    # Color Recovery:
    # We use the image on black to recover the color, dividing by alpha
    # to un-premultiply it (brighten the semi-transparent pixels)
    
    # Avoid division by zero - use a mask for pixels with alpha > 0.01
    alpha_safe = np.where(alpha > 0.01, alpha, 1.0)  # Replace near-zero with 1 to avoid div/0
    
    # Recover foreground color from the version on black
    # (C - (1-alpha) * BG) / alpha
    # Since BG is black (0,0,0), this simplifies to C / alpha
    r_out = img_black[:, :, 0] / alpha_safe
    g_out = img_black[:, :, 1] / alpha_safe
    b_out = img_black[:, :, 2] / alpha_safe
    
    # For pixels with alpha <= 0.01, set color to 0
    r_out = np.where(alpha > 0.01, r_out, 0)
    g_out = np.where(alpha > 0.01, g_out, 0)
    b_out = np.where(alpha > 0.01, b_out, 0)
    
    # Clamp to 0-255 and convert to uint8
    r_out = np.clip(np.round(r_out), 0, 255).astype(np.uint8)
    g_out = np.clip(np.round(g_out), 0, 255).astype(np.uint8)
    b_out = np.clip(np.round(b_out), 0, 255).astype(np.uint8)
    a_out = np.clip(np.round(alpha * 255), 0, 255).astype(np.uint8)
    
    # Stack into RGBA image
    output = np.stack([r_out, g_out, b_out, a_out], axis=2)
    
    # Save as PNG
    Image.fromarray(output, mode="RGBA").save(output_path, "PNG")


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

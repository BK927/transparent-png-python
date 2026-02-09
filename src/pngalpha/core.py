"""
Core image processing logic for pngalpha.
"""

from __future__ import annotations

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
    # sqrt(255^2 + 255^2 + 255^2) ~= 441.67
    bg_dist = np.sqrt(3.0 * 255 * 255)

    # Calculate distance between corresponding observed pixels
    pixel_dist = np.sqrt(
        (img_white[:, :, 0] - img_black[:, :, 0]) ** 2
        + (img_white[:, :, 1] - img_black[:, :, 1]) ** 2
        + (img_white[:, :, 2] - img_black[:, :, 2]) ** 2
    )

    # Opaque pixels look the same on both backgrounds; transparent do not.
    alpha = 1.0 - (pixel_dist / bg_dist)
    alpha = np.clip(alpha, 0.0, 1.0)

    # Avoid division by zero while un-premultiplying color.
    alpha_safe = np.where(alpha > 0.01, alpha, 1.0)

    # Recover foreground color from image on black background.
    r_out = img_black[:, :, 0] / alpha_safe
    g_out = img_black[:, :, 1] / alpha_safe
    b_out = img_black[:, :, 2] / alpha_safe

    # Zero color in near-fully transparent pixels.
    r_out = np.where(alpha > 0.01, r_out, 0)
    g_out = np.where(alpha > 0.01, g_out, 0)
    b_out = np.where(alpha > 0.01, b_out, 0)

    # Clamp and convert to uint8
    r_out = np.clip(np.round(r_out), 0, 255).astype(np.uint8)
    g_out = np.clip(np.round(g_out), 0, 255).astype(np.uint8)
    b_out = np.clip(np.round(b_out), 0, 255).astype(np.uint8)
    a_out = np.clip(np.round(alpha * 255), 0, 255).astype(np.uint8)

    # Stack into RGBA and save
    output = np.stack([r_out, g_out, b_out, a_out], axis=2)
    Image.fromarray(output, mode="RGBA").save(output_path, "PNG")

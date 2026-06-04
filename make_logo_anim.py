#!/usr/bin/env python3
"""
Generate peacock-logo-anim.apng — eye-blink animation from peacock-logo-img.png.

The logo is a stylised peacock feather with a large central eye.
This script animates the eyelid sweeping down and back up for a natural blink.

Usage: python3 make_logo_anim.py
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path(__file__).parent / "peacock-logo-img.png"
DST = Path(__file__).parent / "peacock-logo-anim.apng"

img = Image.open(SRC).convert("RGBA")
W, H = img.size       # 721 x 874
base = np.array(img)  # shape (874, 721, 4)

# ── Eye region (empirically measured from the logo) ──────────────────────────
EYE_CX = W // 2          # 360 — horizontally centred
EYE_CY = int(H * 0.515)  # 450 — slightly below vertical centre
EYE_RX = int(W * 0.141)  # 102 — horizontal radius
EYE_RY = int(H * 0.093)  # 81  — vertical radius

# Dark purple matching the existing upper eyelid in the logo
EYELID_RGBA = np.array([16, 8, 48, 255], dtype=np.uint8)

# ── Grid of pixel coordinates (computed once) ────────────────────────────────
ys, xs = np.mgrid[:H, :W]
# Normalised ellipse distance: 1.0 = on the ellipse edge
ellipse_dist = ((xs - EYE_CX) / EYE_RX) ** 2 + ((ys - EYE_CY) / EYE_RY) ** 2
inside_eye = ellipse_dist <= 1.0  # boolean mask, shape (H, W)


def ease_in_out(t: float) -> float:
    """Smooth cosine ease so the blink accelerates and decelerates naturally."""
    return (1.0 - math.cos(math.pi * t)) / 2.0


def make_frame(t: float) -> Image.Image:
    """
    Build one APNG frame.
    t=0.0 → eye fully open (unchanged)
    t=1.0 → eye fully closed (eyelid covers entire eye oval)
    """
    if t <= 0.0:
        return img.copy()

    pixels = base.copy()

    # Eyelid descends from the top of the ellipse (EYE_CY - EYE_RY)
    # to the bottom (EYE_CY + EYE_RY) as t goes 0→1.
    lid_y = EYE_CY - EYE_RY + (2 * EYE_RY * t)

    # Pixels covered: inside the eye ellipse AND above the current lid line
    lid_mask = inside_eye & (ys <= lid_y)
    pixels[lid_mask] = EYELID_RGBA

    return Image.fromarray(pixels, "RGBA")


# ── Build frame sequence ─────────────────────────────────────────────────────
frames: list[Image.Image] = []
durations: list[int] = []   # milliseconds per frame

HOLD_MS   = 2000   # hold open before blink
CLOSE_MS  = 45     # ms per closing frame (fast)
CLOSED_MS = 130    # hold closed
OPEN_MS   = 45     # ms per opening frame (fast)
BLINK_N   = 7      # frames in each half of the blink

# 1. Hold open
frames.append(make_frame(0.0))
durations.append(HOLD_MS)

# 2. Close (ease-in)
for i in range(1, BLINK_N + 1):
    frames.append(make_frame(ease_in_out(i / BLINK_N)))
    durations.append(CLOSE_MS)

# 3. Hold closed
frames.append(make_frame(1.0))
durations.append(CLOSED_MS)

# 4. Open (ease-out, reverse of close)
for i in range(BLINK_N - 1, -1, -1):
    frames.append(make_frame(ease_in_out(i / BLINK_N)))
    durations.append(OPEN_MS)

# ── Save ─────────────────────────────────────────────────────────────────────
frames[0].save(
    DST,
    format="PNG",
    save_all=True,
    append_images=frames[1:],
    loop=0,         # infinite loop
    duration=durations,
    disposal=2,     # restore background between frames
)

total_ms = sum(durations)
print(f"✅  Saved {len(frames)} frames → {DST.name}")
print(f"    Size : {W}×{H} px")
print(f"    Loop : {total_ms/1000:.2f}s  ({len(frames)} frames)")

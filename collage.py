import cv2
import numpy as np
import math

def make_collage(images, max_cols=4):
    if not images:
        return None

    h, w = images[0].shape[:2]
    cols = min(max_cols, len(images))
    rows = math.ceil(len(images) / cols)

    # If grayscale, convert to 3-channel for consistency (optional)
    processed = []
    for img in images:
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        processed.append(img)

    # Pad list with blank images to fill grid
    blank = np.zeros((h, w, 3), dtype=np.uint8)
    while len(processed) < rows * cols:
        processed.append(blank)

    # Build rows
    grid_rows = []
    for r in range(rows):
        row_imgs = processed[r * cols:(r + 1) * cols]
        row = np.hstack(row_imgs)
        grid_rows.append(row)

    # Stack rows vertically
    collage = np.vstack(grid_rows)
    return collage
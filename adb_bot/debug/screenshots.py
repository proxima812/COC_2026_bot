from __future__ import annotations

import os
import time


def save_unknown_screen(frame_png: bytes) -> str:
    directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_artifacts")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "unknown-{0}.png".format(time.strftime("%Y%m%d-%H%M%S")))
    with open(path, "wb") as handle:
        handle.write(frame_png)
    return path

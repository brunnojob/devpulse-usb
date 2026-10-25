"""Compile a temporary fixture. Never flash or modify the user's board profile."""

import shutil
import subprocess
import tempfile
from pathlib import Path

PROFILE = """#pragma once
#define BOARD_CONFIGURED 1
#define LCD_MOSI 7
#define LCD_SCLK 6
#define LCD_CS 14
#define LCD_DC 15
#define LCD_RST 21
#define LCD_BL -1
#define LCD_BL_ACTIVE HIGH
#define LCD_WIDTH 240
#define LCD_HEIGHT 320
#define LCD_ROTATION 1
"""


def main() -> int:
    source = Path(__file__).resolve().parents[1] / "firmware" / "DevPulse"
    with tempfile.TemporaryDirectory(prefix="devpulse-compile-") as temp:
        sketch = Path(temp) / "DevPulse"
        shutil.copytree(source, sketch)
        (sketch / "board_config.h").write_text(PROFILE)
        print("Compile-only fixture; these pins do not identify a supported board.", flush=True)
        result = subprocess.run(
            ["arduino-cli", "compile", "--fqbn", "esp32:esp32:esp32c6", str(sketch)],
            check=False,
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Monthly strategy rollup. Usage: python -m scripts.run_monthly"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_period  # noqa: E402

if __name__ == "__main__":
    run_period("month")

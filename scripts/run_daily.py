#!/usr/bin/env python3
"""Entry point for daily run. Usage: python -m scripts.run_daily"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_daily  # noqa: E402

if __name__ == "__main__":
    run_daily()

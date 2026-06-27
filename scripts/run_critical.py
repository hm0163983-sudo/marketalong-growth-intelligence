#!/usr/bin/env python3
"""Critical-alert check. Usage: python -m scripts.run_critical"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_critical  # noqa: E402

if __name__ == "__main__":
    run_critical()

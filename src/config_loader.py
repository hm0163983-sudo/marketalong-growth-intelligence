"""Load YAML config from config/. One place, cached."""
from __future__ import annotations

import functools
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@functools.lru_cache(maxsize=None)
def load(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Missing config: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sources() -> list:
    return load("sources").get("sources", [])


def competitors() -> list:
    return load("competitors").get("competitors", [])


def keywords() -> dict:
    return load("keywords")


def scoring() -> dict:
    return load("scoring_weights")


def profile() -> dict:
    try:
        return load("profile").get("profile", {})
    except FileNotFoundError:
        return {}

"""Ruta de datos persistentes (local o disco Render)."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_data_dir() -> str:
    path = os.environ.get("GSP_DATA_DIR", os.path.join(BASE_DIR, "data"))
    os.makedirs(path, exist_ok=True)
    return path

"""Copy the engines into backend/packages so the Function App can be published on its own.

    python tools/package_backend.py
    cd backend && func azure functionapp publish <name>-func --python
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import BACKEND, PLATFORM, SRC  # noqa: E402

TARGET = BACKEND / "packages"


def main():
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    for pkg in ("adlc_workbook", "adlc_excel", "adlc_pii"):
        shutil.copytree(SRC / pkg, TARGET / pkg, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"copied {pkg}")
    print(f"Ready: {TARGET.relative_to(PLATFORM)} - now publish the backend folder.")


if __name__ == "__main__":
    main()

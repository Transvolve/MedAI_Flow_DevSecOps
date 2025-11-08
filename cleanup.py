# cleanup.py
import glob
import shutil
from pathlib import Path

# Folders/files to purge locally and in CI
PATTERNS = [
    "**/__pycache__",
    "**/*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "htmlcov",
    ".coverage",
]

def _clean_path(p: str) -> None:
    path = Path(p)
    if not path.exists():
        return
    if path.is_file():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path, ignore_errors=True)

def main() -> None:
    for pattern in PATTERNS:
        for match in glob.glob(pattern, recursive=True):
            _clean_path(match)

if __name__ == "__main__":
    main()

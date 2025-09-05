# Ensure src layout is importable without installing the package
import sys
import pathlib
root = pathlib.Path(__file__).resolve().parents[1]
src_path = root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

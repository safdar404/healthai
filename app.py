"""Streamlit entrypoint. Keep this at the repository root for Cloud deployment."""
from pathlib import Path
import runpy
import sys

SOURCE = Path(__file__).resolve().parent / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))
runpy.run_path(str(SOURCE / "app.py"), run_name="__main__")

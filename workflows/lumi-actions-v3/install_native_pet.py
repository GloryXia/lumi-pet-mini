"""Compatibility entry point for the portable, validated installer."""
from pathlib import Path
import runpy
import sys

tools = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(tools))
runpy.run_path(str(tools / 'install_pet.py'), run_name='__main__')

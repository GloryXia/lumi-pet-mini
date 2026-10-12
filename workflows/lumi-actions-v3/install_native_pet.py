"""Compatibility entry point for the native Codex App project installer."""
from pathlib import Path
import sys

tools = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(tools))
from native_pet import main

if __name__ == '__main__':
    raise SystemExit(main(['install', *sys.argv[1:]]))

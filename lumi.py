#!/usr/bin/env python3
"""Repository entry point for Codex App native Pet/Mini package management."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
from native_pet import main

if __name__ == '__main__':
    raise SystemExit(main())

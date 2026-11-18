#!/usr/bin/env python3
"""FontWorks: a type foundry for Claude and other AI agents. Run with no arguments for help."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pc.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

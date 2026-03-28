#!/usr/bin/env python3
"""
Main entry point for the AI Trading Bot.
Handles both live trading and dashboard modes.
"""

import sys
import logging
from src.main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    sys.exit(main())

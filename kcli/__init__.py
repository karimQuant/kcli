"""KCLI - Local Knowledge Base CLI."""

__version__ = "0.1.0"


import logging

from rich.console import Console

import kcli.storage as storage

storage.configure()

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
console = Console()

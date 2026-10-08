"""
services/logger.py
------------------
Structured logger for parrhet.ai.

Writes to:
  1. A rotating log file  (logs/rhet.log — always)
  2. Azure Application Insights (when APPLICATIONINSIGHTS_CONNECTION_STRING
     is present in the environment — works automatically on deployment)

Usage
-----
    from services.logger import rhet_log

    rhet_log.info("Something happened")
    rhet_log.warning("Non-critical issue", extra={"context": "pipeline"})
    rhet_log.error("Something broke", exc_info=True)

Never surface these messages to the user — they are for the developer.
"""

import logging
import logging.handlers
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ #
# Log directory                                                        #
# ------------------------------------------------------------------ #

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "rhet.log"

# ------------------------------------------------------------------ #
# Build the logger                                                     #
# ------------------------------------------------------------------ #

_logger = logging.getLogger("rhet")
_logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers on Streamlit hot-reloads.
if not _logger.handlers:

    # Shared formatter — structured, easy to grep.
    _fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # ── 1. Rotating file handler (always active) ──────────────────────
    _file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB per file
        backupCount=3,               # keep rhet.log + 3 rotated copies
        encoding="utf-8",
    )
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_fmt)
    _logger.addHandler(_file_handler)

    # ── 2. Azure Application Insights (active when env var is set) ────
    _conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if _conn_str:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            # configure_azure_monitor instruments the standard logging module
            # automatically once called.  All records emitted by _logger
            # (and its children) will be exported to Application Insights.
            configure_azure_monitor(connection_string=_conn_str)
            _logger.info(
                "Azure Application Insights configured — telemetry active."
            )
        except Exception as _ai_err:
            # Do not crash if App Insights setup fails — fall back to file only.
            _logger.warning(
                "Application Insights setup failed: %s — logging to file only.",
                _ai_err,
            )

# ------------------------------------------------------------------ #
# Public handle                                                        #
# ------------------------------------------------------------------ #

#: Use this everywhere in the app instead of print() or st.warning().
rhet_log = _logger

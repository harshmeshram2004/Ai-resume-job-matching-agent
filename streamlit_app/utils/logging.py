"""Lightweight, privacy-conscious logger."""
from __future__ import annotations
import logging
import sys

_logger = logging.getLogger("resume_agent")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    _logger.addHandler(h)


def log(msg: str) -> None:
    _logger.info(msg)


def warn(msg: str) -> None:
    _logger.warning(msg)


def error(msg: str) -> None:
    _logger.error(msg)

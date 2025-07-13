# -*- coding: utf-8 -*-
"""Simplified logging configuration for the Mengshen Font project."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False,
) -> None:
    """Set up logging configuration for the application.

    Args:
        level: Base logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        verbose: Enable verbose output (DEBUG level)
        quiet: Minimize output (WARNING+ only)
    """
    # Determine effective log level
    if quiet:
        effective_level = logging.WARNING
    elif verbose:
        effective_level = logging.DEBUG
    else:
        effective_level = getattr(logging, level.upper(), logging.INFO)

    # Simple formatter
    formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(formatter)

    # File handler (if specified)
    handlers: list[logging.Handler] = [console_handler]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        force=True,
    )


def get_logger(name: str = "mengshen") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to 'mengshen')

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Backward compatibility functions
def get_cli_logger() -> logging.Logger:
    """Get logger for CLI operations."""
    return get_logger("mengshen.cli")


def get_builder_logger() -> logging.Logger:
    """Get logger for font building operations."""
    return get_logger("mengshen.builder")


def get_debug_logger() -> logging.Logger:
    """Get logger for debug information."""
    return get_logger("mengshen.debug")


def get_scripts_logger() -> logging.Logger:
    """Get logger for script operations."""
    return get_logger("mengshen.scripts")

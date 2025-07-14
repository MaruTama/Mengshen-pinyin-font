# -*- coding: utf-8 -*-
"""Logging configuration for the Mengshen Font project."""

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

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(simple_formatter)

    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(detailed_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything, handlers will filter
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Set specific logger levels
    logging.getLogger("mengshen.cli").setLevel(effective_level)
    logging.getLogger("mengshen.builder").setLevel(effective_level)
    logging.getLogger("mengshen.debug").setLevel(
        logging.DEBUG if verbose else logging.INFO
    )
    logging.getLogger("mengshen.scripts").setLevel(effective_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the standard naming convention.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    # Convert module name to hierarchical logger name
    if name.startswith("refactored."):
        logger_name = name.replace("refactored.", "mengshen.", 1)
    else:
        logger_name = f"mengshen.{name}"

    return logging.getLogger(logger_name)


def get_cli_logger() -> logging.Logger:
    """Get logger for CLI operations."""
    return logging.getLogger("mengshen.cli")


def get_builder_logger() -> logging.Logger:
    """Get logger for font building operations."""
    return logging.getLogger("mengshen.builder")


def get_debug_logger() -> logging.Logger:
    """Get logger for debug information."""
    return logging.getLogger("mengshen.debug")


def get_scripts_logger() -> logging.Logger:
    """Get logger for script operations."""
    return logging.getLogger("mengshen.scripts")


# Configuration for different environments
LOGGING_CONFIGS = {
    "development": {
        "level": "DEBUG",
        "verbose": True,
        "log_file": Path("logs/mengshen_dev.log"),
    },
    "production": {
        "level": "INFO",
        "verbose": False,
        "log_file": Path("logs/mengshen.log"),
    },
    "testing": {
        "level": "WARNING",
        "verbose": False,
        "log_file": None,  # No file logging during tests
    },
    "ci": {
        "level": "INFO",
        "verbose": False,
        "log_file": Path("logs/mengshen_ci.log"),
    },
}


def setup_environment_logging(environment: str = "production") -> None:
    """Set up logging for a specific environment.

    Args:
        environment: Environment name (development, production, testing, ci)
    """
    config = LOGGING_CONFIGS.get(environment, LOGGING_CONFIGS["production"])
    setup_logging(**config)


# Suppress verbose third-party logging
def suppress_third_party_logs():
    """Suppress verbose logging from third-party libraries."""
    # Common third-party loggers that can be noisy
    third_party_loggers = [
        "urllib3",
        "requests",
        "fontTools",
        "PIL",
        "matplotlib",
    ]

    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

# -*- coding: utf-8 -*-
"""Structured, translatable API errors.

Error responses carry a machine-readable ``code`` plus an English
``message`` fallback and interpolation ``params``; the frontend maps the
code to a localized string. The English message keeps the raw API and the
tests readable without a translation layer.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def problem(status_code: int, code: str, message: str, **params: Any) -> HTTPException:
    """Build an HTTPException whose detail is a structured error object."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "params": params},
    )


class FontValidationError(ValueError):
    """A font upload failed validation, with a translatable code."""

    def __init__(self, code: str, message: str, **params: Any):
        super().__init__(message)
        self.code = code
        self.message = message
        self.params = params

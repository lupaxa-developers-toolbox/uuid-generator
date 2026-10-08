"""Errors raised by ``lupaxa.uuid_generator``."""

from __future__ import annotations


class UUIDGeneratorError(ValueError):
    """Raised when a UUID cannot be generated, formatted, or decoded."""

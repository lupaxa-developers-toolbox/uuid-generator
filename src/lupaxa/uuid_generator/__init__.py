"""lupaxa.uuid_generator — UUID versions 1, 3, 4, 5, 6, 7, and 8, plus formatting.

``UUIDGenerator.generate_uuid()`` returns one identifier. Pass a config
mapping for version, namespace, name, case, separators, length, and
prefix or suffix. Custom character sets, Base64 encoding, and hashing
are on the same class.
"""

from __future__ import annotations

from .exceptions import UUIDGeneratorError
from .generator import UUIDGenerator
from .version import __version__, get_version

__all__ = [
    "UUIDGenerator",
    "UUIDGeneratorError",
    "__version__",
    "get_version",
]

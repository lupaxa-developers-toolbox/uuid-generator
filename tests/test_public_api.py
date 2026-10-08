"""Public export surface."""

from __future__ import annotations

import lupaxa.uuid_generator as uuid_generator


def test_public_names_are_exported() -> None:
    for name in (
        "UUIDGenerator",
        "UUIDGeneratorError",
        "__version__",
        "get_version",
    ):
        assert hasattr(uuid_generator, name)
        assert name in uuid_generator.__all__

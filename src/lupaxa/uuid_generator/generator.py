"""UUID generation and formatting."""

from __future__ import annotations

import base64
import hashlib
import os
import random
import time
import uuid
from collections.abc import Mapping, Sequence
from threading import Lock
from typing import Any

from .exceptions import UUIDGeneratorError

_UUID7_LOCK = Lock()
_uuid7_last_ms = -1
_uuid7_seq = 0


def _uuid6() -> uuid.UUID:
    """Return an RFC 9562 UUID version 6.

    Built from ``uuid1`` with the 60-bit timestamp reordered so the
    most significant bits come first. The clock sequence and node are
    unchanged.
    """
    source = uuid.uuid1()
    time_low_v1 = source.time_low
    time_mid_v1 = source.time_mid
    time_hi_v1 = source.time_hi_version & 0x0FFF
    time_high = (time_hi_v1 << 20) | (time_mid_v1 << 4) | (time_low_v1 >> 28)
    time_mid = (time_low_v1 >> 12) & 0xFFFF
    time_low = time_low_v1 & 0xFFF
    value = time_high << 96
    value |= time_mid << 80
    value |= 0x6 << 76
    value |= time_low << 64
    value |= 0b10 << 62
    value |= (source.clock_seq & 0x3FFF) << 48
    value |= source.node & 0xFFFFFFFFFFFF
    return uuid.UUID(int=value)


def _uuid7() -> uuid.UUID:
    """Return an RFC 9562 UUID version 7.

    The first 48 bits are Unix time in milliseconds. A 12-bit counter
    keeps values increasing when several are created in the same
    millisecond, including if the clock steps backwards.
    """
    global _uuid7_last_ms, _uuid7_seq

    now_ms = time.time_ns() // 1_000_000
    with _UUID7_LOCK:
        if now_ms > _uuid7_last_ms:
            _uuid7_last_ms = now_ms
            _uuid7_seq = int.from_bytes(os.urandom(2), "big") & 0xFFF
        else:
            _uuid7_seq = (_uuid7_seq + 1) & 0xFFF
            if _uuid7_seq == 0:
                _uuid7_last_ms += 1
                _uuid7_seq = int.from_bytes(os.urandom(2), "big") & 0xFFF
        timestamp_ms = _uuid7_last_ms
        rand_a = _uuid7_seq

    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF
    value = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return uuid.UUID(int=value)


def _uuid8(a: int | None = None, b: int | None = None, c: int | None = None) -> uuid.UUID:
    """Return an RFC 9562 UUID version 8, matching ``uuid.uuid8(a, b, c)``.

    ``a`` is 48 bits, ``b`` is 12 bits, and ``c`` is 62 bits. Wider
    integers keep their least significant bits. An omitted block is
    filled with ``random.getrandbits``, the same generator the standard
    library uses.
    """
    for label, block in (("a", a), ("b", b), ("c", c)):
        if block is not None and not isinstance(block, int):
            raise UUIDGeneratorError(f"Block {label} must be an integer.")
    if a is None:
        a = random.getrandbits(48)
    if b is None:
        b = random.getrandbits(12)
    if c is None:
        c = random.getrandbits(62)
    value = (a & 0xFFFFFFFFFFFF) << 80
    value |= (b & 0xFFF) << 64
    value |= c & 0x3FFFFFFFFFFFFFFF
    value |= (8 << 76) | (0x8000 << 48)
    return uuid.UUID(int=value)


class UUIDGenerator:
    """Generate and format UUID strings.

    Methods are stateless. ``generate_uuid`` applies version, format,
    prefix, and suffix from one config mapping. A ``custom_char_set``
    skips UUID versions and draws from that alphabet instead.
    """

    @staticmethod
    def create_uuid(
        version: int = 4,
        namespace: uuid.UUID | None = None,
        name: str | None = None,
        a: int | None = None,
        b: int | None = None,
        c: int | None = None,
    ) -> str:
        """Return a UUID string for version 1, 3, 4, 5, 6, 7, or 8.

        Versions 3 and 5 require both ``namespace`` and ``name``.
        Version 6 reorders the version 1 timestamp so values sort.
        Version 7 is time-ordered from the Unix time in milliseconds.
        Version 8 takes the same ``a``, ``b``, and ``c`` blocks as
        ``uuid.uuid8``.
        """
        if version not in (1, 3, 4, 5, 6, 7, 8):
            raise UUIDGeneratorError("Unsupported UUID version. Use 1, 3, 4, 5, 6, 7, or 8.")
        if version != 8 and (a is not None or b is not None or c is not None):
            raise UUIDGeneratorError("Blocks a, b, and c apply only to UUID version 8.")
        if version == 1:
            return str(uuid.uuid1())
        if version == 3:
            if namespace is None or name is None:
                raise UUIDGeneratorError("Both 'namespace' and 'name' are required for UUIDv3.")
            return str(uuid.uuid3(namespace, name))
        if version == 4:
            return str(uuid.uuid4())
        if version == 5:
            if namespace is None or name is None:
                raise UUIDGeneratorError("Both 'namespace' and 'name' are required for UUIDv5.")
            return str(uuid.uuid5(namespace, name))
        if version == 6:
            return str(_uuid6())
        if version == 7:
            return str(_uuid7())
        return str(_uuid8(a, b, c))

    @staticmethod
    def apply_format(
        uuid_string: str,
        format_type: str = "standard",
        separator: str = "-",
        length: int | None = None,
    ) -> str:
        """Apply case, separator, and optional truncation.

        ``format_type`` is ``standard``, ``uppercase``, ``lowercase``,
        or ``no-dashes``. Other values leave the text unchanged before
        the separator and length steps.
        """
        if format_type == "uppercase":
            uuid_string = uuid_string.upper()
        elif format_type == "lowercase":
            uuid_string = uuid_string.lower()
        elif format_type == "no-dashes":
            uuid_string = uuid_string.replace("-", "")

        if separator != "-" and "-" in uuid_string:
            uuid_string = uuid_string.replace("-", separator)

        if length is not None and length > 0:
            uuid_string = uuid_string[:length]

        return uuid_string

    @staticmethod
    def add_prefix_suffix(uuid_string: str, prefix: str = "", suffix: str = "") -> str:
        """Return ``uuid_string`` with ``prefix`` and ``suffix`` attached."""
        return f"{prefix}{uuid_string}{suffix}"

    @staticmethod
    def generate_custom_uuid(char_set: str, length: int) -> str:
        """Return ``length`` characters drawn from ``char_set``."""
        if not char_set:
            raise UUIDGeneratorError("Character set must not be empty.")
        if not length or length <= 0:
            raise UUIDGeneratorError("Length must be specified and greater than 0.")
        return "".join(random.choice(char_set) for _ in range(length))

    @staticmethod
    def generate_uuid(config: Mapping[str, Any] | None = None) -> str:
        """Generate one identifier from a config mapping.

        Keys: ``version``, ``namespace``, ``name``, ``a``, ``b``, ``c``,
        ``format_type``, ``separator``, ``length``, ``prefix``,
        ``suffix``, ``custom_char_set``. When ``custom_char_set`` is
        set, ``length`` is required and UUID version options are ignored.
        ``a``, ``b``, and ``c`` are the version 8 blocks from
        ``uuid.uuid8``.
        """
        options = dict(config or {})
        version = options.get("version", 4)
        namespace = options.get("namespace")
        name = options.get("name")
        format_type = options.get("format_type", "standard")
        separator = options.get("separator", "-")
        length = options.get("length")
        prefix = options.get("prefix", "")
        suffix = options.get("suffix", "")
        custom_char_set = options.get("custom_char_set")
        block_a = options.get("a")
        block_b = options.get("b")
        block_c = options.get("c")

        if not isinstance(version, int) or isinstance(version, bool):
            raise UUIDGeneratorError("Unsupported UUID version. Use 1, 3, 4, 5, 6, 7, or 8.")
        if namespace is not None and not isinstance(namespace, uuid.UUID):
            raise UUIDGeneratorError("Namespace must be a uuid.UUID.")
        if name is not None and not isinstance(name, str):
            raise UUIDGeneratorError("Name must be a string.")
        if not isinstance(format_type, str) or not isinstance(separator, str):
            raise UUIDGeneratorError("Format type and separator must be strings.")
        if length is not None and (not isinstance(length, int) or isinstance(length, bool)):
            raise UUIDGeneratorError("Length must be an integer.")
        if not isinstance(prefix, str) or not isinstance(suffix, str):
            raise UUIDGeneratorError("Prefix and suffix must be strings.")

        if custom_char_set is not None:
            if not isinstance(custom_char_set, str):
                raise UUIDGeneratorError("Custom character set must be a string.")
            if length is None:
                raise UUIDGeneratorError("Length must be specified and greater than 0.")
            uuid_string = UUIDGenerator.generate_custom_uuid(custom_char_set, length)
        else:
            uuid_string = UUIDGenerator.create_uuid(
                version=version,
                namespace=namespace,
                name=name,
                a=block_a,
                b=block_b,
                c=block_c,
            )
            uuid_string = UUIDGenerator.apply_format(
                uuid_string,
                format_type=format_type,
                separator=separator,
                length=length,
            )

        return UUIDGenerator.add_prefix_suffix(uuid_string, prefix=prefix, suffix=suffix)

    @staticmethod
    def encode_uuid(uuid_string: str) -> str:
        """Return the URL-safe Base64 form of a canonical UUID, without padding."""
        try:
            uuid_bytes = uuid.UUID(uuid_string).bytes
        except (ValueError, AttributeError, TypeError) as exc:
            raise UUIDGeneratorError(f"Error encoding UUID: {exc}") from exc
        return base64.urlsafe_b64encode(uuid_bytes).rstrip(b"=").decode("ascii")

    @staticmethod
    def decode_uuid(encoded_uuid: str) -> str:
        """Return the canonical UUID for a URL-safe Base64 value from ``encode_uuid``."""
        try:
            decoded_bytes = base64.urlsafe_b64decode(encoded_uuid + "==")
            return str(uuid.UUID(bytes=decoded_bytes))
        except (ValueError, TypeError) as exc:
            raise UUIDGeneratorError(f"Error decoding UUID: {exc}") from exc

    @staticmethod
    def hash_uuid(uuid_string: str, hash_algorithm: str = "sha256") -> str:
        """Return the hex digest of ``uuid_string`` using ``sha256`` or ``md5``."""
        encoded = uuid_string.encode("utf-8")
        if hash_algorithm == "sha256":
            return hashlib.sha256(encoded).hexdigest()
        if hash_algorithm == "md5":
            return hashlib.md5(encoded, usedforsecurity=False).hexdigest()
        raise UUIDGeneratorError(f"Unsupported hash algorithm: {hash_algorithm}")

    @staticmethod
    def generate_unique_uuid(
        existing_uuids: Sequence[str],
        attempts: int = 3,
        config: Mapping[str, Any] | None = None,
    ) -> str:
        """Return a UUID that is not already in ``existing_uuids``.

        Raises ``UUIDGeneratorError`` when every attempt collides.
        """
        if attempts < 1:
            raise UUIDGeneratorError(f"Failed to generate a unique UUID after {attempts} attempts.")
        seen = set(existing_uuids)
        for _ in range(attempts):
            new_uuid = UUIDGenerator.generate_uuid(config)
            if new_uuid not in seen:
                return new_uuid
        raise UUIDGeneratorError(f"Failed to generate a unique UUID after {attempts} attempts.")

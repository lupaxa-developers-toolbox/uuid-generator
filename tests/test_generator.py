"""Tests for UUID generation and formatting."""

from __future__ import annotations

import hashlib
import time
import uuid

import pytest

from lupaxa.uuid_generator import UUIDGenerator, UUIDGeneratorError


def test_version_4_shape() -> None:
    value = UUIDGenerator.create_uuid()
    parsed = uuid.UUID(value)
    assert parsed.version == 4


def test_version_1_shape() -> None:
    parsed = uuid.UUID(UUIDGenerator.create_uuid(version=1))
    assert parsed.version == 1


def test_version_5_is_deterministic() -> None:
    expected = str(uuid.uuid5(uuid.NAMESPACE_DNS, "example.com"))
    assert UUIDGenerator.create_uuid(5, uuid.NAMESPACE_DNS, "example.com") == expected


def test_version_3_is_deterministic() -> None:
    expected = str(uuid.uuid3(uuid.NAMESPACE_URL, "https://example.com"))
    got = UUIDGenerator.generate_uuid(
        {"version": 3, "namespace": uuid.NAMESPACE_URL, "name": "https://example.com"}
    )
    assert got == expected


@pytest.mark.parametrize("version", [3, 5])
def test_namespaced_versions_require_both_inputs(version: int) -> None:
    with pytest.raises(UUIDGeneratorError, match="namespace"):
        UUIDGenerator.create_uuid(version=version, name="only-name")


def _uuid6_timestamp(value: uuid.UUID) -> int:
    time_high = value.int >> 96
    time_mid = (value.int >> 80) & 0xFFFF
    time_low = (value.int >> 64) & 0xFFF
    return (time_high << 28) | (time_mid << 12) | time_low


def test_version_6_reorders_version_1(monkeypatch: pytest.MonkeyPatch) -> None:
    source = uuid.UUID("12345678-9abc-1def-8234-567890abcdef")
    monkeypatch.setattr("lupaxa.uuid_generator.generator.uuid.uuid1", lambda: source)
    got = uuid.UUID(UUIDGenerator.create_uuid(version=6))
    assert got.version == 6
    assert got.variant == uuid.RFC_4122
    assert got.node == source.node
    assert got.clock_seq == source.clock_seq
    assert _uuid6_timestamp(got) == source.time


def test_version_6_sorts_by_creation() -> None:
    values = [uuid.UUID(UUIDGenerator.create_uuid(version=6)) for _ in range(16)]
    now = time.time_ns() // 100 + 0x01B21DD213814000
    assert all(item.version == 6 for item in values)
    assert all(abs(_uuid6_timestamp(item) - now) < 50_000_000 for item in values)
    integers = [item.int for item in values]
    assert integers == sorted(integers)
    assert len(set(integers)) == len(integers)


def test_version_7_is_time_ordered() -> None:
    values = [uuid.UUID(UUIDGenerator.create_uuid(version=7)) for _ in range(32)]
    now_ms = time.time_ns() // 1_000_000
    assert all(item.version == 7 for item in values)
    assert all(item.variant == uuid.RFC_4122 for item in values)
    assert all(abs((item.int >> 80) - now_ms) < 5_000 for item in values)
    assert [item.int for item in values] == sorted(item.int for item in values)
    assert len({item.int for item in values}) == len(values)


def test_version_8_matches_stdlib_blocks() -> None:
    got = UUIDGenerator.create_uuid(8, a=0x12345678, b=0x9ABCDEF0, c=0x11223344)
    assert got == "00001234-5678-8ef0-8000-000011223344"


def test_version_8_keeps_low_bits_only() -> None:
    narrow = UUIDGenerator.create_uuid(8, a=0x12345678, b=0xEF0, c=0x11223344)
    wide = UUIDGenerator.create_uuid(8, a=0x1_0000_1234_5678, b=0x9ABCDEF0, c=0x11223344)
    assert narrow == wide == "00001234-5678-8ef0-8000-000011223344"


def test_version_8_from_config() -> None:
    got = UUIDGenerator.generate_uuid(
        {"version": 8, "a": 0x12345678, "b": 0x9ABCDEF0, "c": 0x11223344}
    )
    assert got == "00001234-5678-8ef0-8000-000011223344"


def test_version_8_omitted_blocks_are_random() -> None:
    values = [uuid.UUID(UUIDGenerator.create_uuid(version=8)) for _ in range(8)]
    assert all(item.version == 8 for item in values)
    assert all(item.variant == uuid.RFC_4122 for item in values)
    assert len({item.int for item in values}) == len(values)


def test_blocks_require_version_8() -> None:
    with pytest.raises(UUIDGeneratorError, match="version 8"):
        UUIDGenerator.create_uuid(version=4, a=1)


def test_unsupported_version() -> None:
    with pytest.raises(UUIDGeneratorError, match="Unsupported UUID version"):
        UUIDGenerator.create_uuid(version=2)


def test_format_options() -> None:
    raw = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert UUIDGenerator.apply_format(raw, format_type="uppercase") == raw.upper()
    assert UUIDGenerator.apply_format(raw, format_type="no-dashes") == raw.replace("-", "")
    assert UUIDGenerator.apply_format(raw, separator="_") == raw.replace("-", "_")
    assert UUIDGenerator.apply_format(raw, length=8) == raw[:8]


def test_prefix_and_suffix() -> None:
    value = UUIDGenerator.generate_uuid({"prefix": "id-", "suffix": "-end", "length": 8})
    assert value.startswith("id-")
    assert value.endswith("-end")


def test_custom_alphabet() -> None:
    value = UUIDGenerator.generate_custom_uuid("ab", 12)
    assert len(value) == 12
    assert set(value) <= set("ab")


def test_custom_alphabet_rejects_bad_input() -> None:
    with pytest.raises(UUIDGeneratorError):
        UUIDGenerator.generate_custom_uuid("", 4)
    with pytest.raises(UUIDGeneratorError):
        UUIDGenerator.generate_uuid({"custom_char_set": "abc"})


def test_encode_round_trip() -> None:
    raw = str(uuid.uuid4())
    encoded = UUIDGenerator.encode_uuid(raw)
    assert "=" not in encoded
    assert UUIDGenerator.decode_uuid(encoded) == raw


def test_encode_rejects_plain_text() -> None:
    with pytest.raises(UUIDGeneratorError, match="encoding"):
        UUIDGenerator.encode_uuid("not-a-uuid")


def test_hash_algorithms() -> None:
    raw = "abc"
    assert UUIDGenerator.hash_uuid(raw) == hashlib.sha256(b"abc").hexdigest()
    assert UUIDGenerator.hash_uuid(raw, "md5") == hashlib.md5(b"abc").hexdigest()
    with pytest.raises(UUIDGeneratorError, match="Unsupported hash"):
        UUIDGenerator.hash_uuid(raw, "sha1")


def test_unique_uuid_skips_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    values = iter(["same", "other"])

    def fake(_config: object = None) -> str:
        return next(values)

    monkeypatch.setattr(UUIDGenerator, "generate_uuid", staticmethod(fake))
    assert UUIDGenerator.generate_unique_uuid(["same"], attempts=3) == "other"


def test_unique_uuid_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(UUIDGenerator, "generate_uuid", staticmethod(lambda _config=None: "same"))
    with pytest.raises(UUIDGeneratorError, match="after 2 attempts"):
        UUIDGenerator.generate_unique_uuid(["same"], attempts=2)

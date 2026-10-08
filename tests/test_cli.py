"""Tests for the uuid-generator CLI."""

from __future__ import annotations

import base64
import os
import pathlib
import subprocess
import sys
import uuid

import pytest

from lupaxa.uuid_generator import UUIDGenerator, __version__
from lupaxa.uuid_generator.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"uuid-generator {__version__}"


def test_default_prints_one_version_4(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    line = capsys.readouterr().out.strip()
    assert uuid.UUID(line).version == 4


def test_count_prints_one_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["-n", "3"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert len(set(lines)) == 3


def test_version_6_prints_a_uuid(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--uuid-version", "6"]) == 0
    assert uuid.UUID(capsys.readouterr().out.strip()).version == 6


def test_version_8_blocks_match_library(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(
            [
                "--uuid-version",
                "8",
                "--a",
                "0x12345678",
                "--b",
                "0x9abcdef0",
                "--c",
                "0x11223344",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "00001234-5678-8ef0-8000-000011223344"


def test_blocks_rejected_for_other_versions() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--a", "1"])
    assert exc.value.code == 2


def test_version_7_prints_a_uuid(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--uuid-version", "7"]) == 0
    assert uuid.UUID(capsys.readouterr().out.strip()).version == 7


def test_base64_and_md5_flags(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--base64"]) == 0
    encoded = capsys.readouterr().out.strip()
    parsed = uuid.UUID(bytes=base64.urlsafe_b64decode(encoded + "=="))
    assert parsed.version == 4

    assert main(["--md5"]) == 0
    digest = capsys.readouterr().out.strip()
    assert len(digest) == 32
    assert all(character in "0123456789abcdef" for character in digest)


def test_base64_and_md5_together(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--base64", "--md5"]) == 0
    encoded, digest = capsys.readouterr().out.split()
    parsed = uuid.UUID(bytes=base64.urlsafe_b64decode(encoded + "=="))
    canonical = str(parsed)
    assert digest == UUIDGenerator.hash_uuid(canonical, "md5")


def test_version_5_is_deterministic(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--uuid-version", "5", "--namespace", "dns", "--name", "example.com"]) == 0
    expected = str(uuid.uuid5(uuid.NAMESPACE_DNS, "example.com"))
    assert capsys.readouterr().out.strip() == expected


def test_format_and_prefix(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--format", "no-dashes", "--prefix", "id-"]) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("id-")
    assert "-" not in line.removeprefix("id-")


def test_named_version_without_name_exits_2() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--uuid-version", "3", "--namespace", "dns"])
    assert exc.value.code == 2


def test_bad_namespace_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--uuid-version", "5", "--namespace", "nope", "--name", "x"]) == 2
    assert "error:" in capsys.readouterr().err


def test_namespace_ignored_on_version_4() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--namespace", "dns"])
    assert exc.value.code == 2


def test_count_must_be_positive() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["-n", "0"])
    assert exc.value.code == 2


def test_module_entry_version() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else src + os.pathsep + env["PYTHONPATH"]
    proc = subprocess.run(
        [sys.executable, "-m", "lupaxa.uuid_generator", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert __version__ in proc.stdout

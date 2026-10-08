"""Package layout."""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "src" / "lupaxa" / "uuid_generator"


def test_namespace_package_has_no_init() -> None:
    assert not (REPO_ROOT / "src" / "lupaxa" / "__init__.py").is_file()


def test_cli_modules_exist() -> None:
    assert (PKG / "cli.py").is_file()
    assert (PKG / "__main__.py").is_file()
    assert (PKG / "py.typed").is_file()


def test_root_script_is_not_the_library() -> None:
    assert not (REPO_ROOT / "generator.py").is_file()
    assert not (REPO_ROOT / "setup.cfg").is_file()
    assert not (REPO_ROOT / "mkdocs.yml").is_file()

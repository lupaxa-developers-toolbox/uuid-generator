"""Command-line interface for lupaxa.uuid_generator."""

from __future__ import annotations

import argparse
import sys
import uuid

from .exceptions import UUIDGeneratorError
from .generator import UUIDGenerator
from .version import __version__

_NAMESPACES = {
    "dns": uuid.NAMESPACE_DNS,
    "url": uuid.NAMESPACE_URL,
    "oid": uuid.NAMESPACE_OID,
    "x500": uuid.NAMESPACE_X500,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a UUID and print it.")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit.",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="How many identifiers to print. Default is 1.",
    )
    parser.add_argument(
        "--uuid-version",
        type=int,
        choices=(1, 3, 4, 5, 6, 7, 8),
        default=4,
        help="UUID version. Default is 4.",
    )
    parser.add_argument(
        "--namespace",
        help="Namespace for version 3 or 5: dns, url, oid, x500, or a UUID.",
    )
    parser.add_argument("--name", help="Name for version 3 or 5.")
    parser.add_argument(
        "--a",
        type=_integer_block,
        help="Version 8 block a (48 bits). Extra high bits are ignored.",
    )
    parser.add_argument(
        "--b",
        type=_integer_block,
        help="Version 8 block b (12 bits). Extra high bits are ignored.",
    )
    parser.add_argument(
        "--c",
        type=_integer_block,
        help="Version 8 block c (62 bits). Extra high bits are ignored.",
    )
    parser.add_argument(
        "--format",
        choices=("standard", "uppercase", "lowercase", "no-dashes"),
        default="standard",
        help="Case and dash layout. Default is standard.",
    )
    parser.add_argument(
        "--separator",
        default="-",
        help="Replace the hyphen. Ignored with --format no-dashes.",
    )
    parser.add_argument(
        "--length",
        type=int,
        help="Keep only the first N characters after formatting.",
    )
    parser.add_argument("--prefix", default="", help="Text to put before each identifier.")
    parser.add_argument("--suffix", default="", help="Text to put after each identifier.")
    parser.add_argument(
        "--base64",
        action="store_true",
        help="Print the URL-safe Base64 form of each UUID.",
    )
    parser.add_argument(
        "--md5",
        action="store_true",
        help="Print the MD5 hex digest of each UUID.",
    )
    return parser


def _integer_block(value: str) -> int:
    """Parse a decimal or ``0x`` hex block the way ``int(value, 0)`` does."""
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer block: {value}") from exc


def resolve_namespace(value: str) -> uuid.UUID:
    """Return a namespace UUID from a well-known name or a UUID string."""
    known = _NAMESPACES.get(value.lower())
    if known is not None:
        return known
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise UUIDGeneratorError("Namespace must be dns, url, oid, x500, or a UUID.") from exc


def render_identifier(value: str, *, base64_encode: bool, md5: bool) -> str:
    """Return the printed form of one generated identifier."""
    parts: list[str] = []
    if base64_encode:
        parts.append(UUIDGenerator.encode_uuid(value))
    if md5:
        parts.append(UUIDGenerator.hash_uuid(value, "md5"))
    if parts:
        return " ".join(parts)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"uuid-generator {__version__}")
        return 0

    if args.count < 1:
        parser.error("count must be at least 1")

    namespace = None
    if args.uuid_version in (3, 5):
        if not args.namespace or args.name is None:
            parser.error("--namespace and --name are required for UUID version 3 or 5")
        try:
            namespace = resolve_namespace(args.namespace)
        except UUIDGeneratorError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    elif args.namespace or args.name:
        parser.error("--namespace and --name apply only to UUID version 3 or 5")

    blocks = (args.a, args.b, args.c)
    if args.uuid_version != 8 and any(block is not None for block in blocks):
        parser.error("--a, --b, and --c apply only to UUID version 8")

    config: dict[str, object] = {
        "version": args.uuid_version,
        "format_type": args.format,
        "separator": args.separator,
        "prefix": args.prefix,
        "suffix": args.suffix,
    }
    if namespace is not None:
        config["namespace"] = namespace
        config["name"] = args.name
    if args.length is not None:
        config["length"] = args.length
    if args.a is not None:
        config["a"] = args.a
    if args.b is not None:
        config["b"] = args.b
    if args.c is not None:
        config["c"] = args.c

    try:
        for _ in range(args.count):
            print(
                render_identifier(
                    UUIDGenerator.generate_uuid(config),
                    base64_encode=args.base64,
                    md5=args.md5,
                )
            )
    except UUIDGeneratorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0

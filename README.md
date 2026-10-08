<p align="center">
  <a href="https://github.com/lupaxa-developers-toolbox">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/developers-toolbox/readme-logo.png" alt="Developers Toolbox" />
  </a>
</p>

<h1 align="center">UUID Generator</h1>

Generate UUID versions 1, 3, 4, 5, 6, 7, and 8. Format the result (case,
separator, length, prefix, suffix), or draw a custom alphabet when a
standard UUID is not what you need. The command can also print each
UUID as URL-safe Base64 or as an MD5 digest.

The PyPI name is `lupaxa-uuid-generator`. The import path is
`lupaxa.uuid_generator`. The console script is `uuid-generator`.
`lupaxa` is a namespace package — there is no `lupaxa/__init__.py`.

Public names: `UUIDGenerator`, `UUIDGeneratorError`, `__version__`,
`get_version()`.

## Install

```bash
pip install lupaxa-uuid-generator
```

Requires Python 3.10+. There are no runtime dependencies.

## Versions

| Version | Example                                | Where to Use                                                                                                   |
| ------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `1`     | `a28f767c-c2f2-11f1-9234-001122334455` | Time and a node. Use when you need to trace the host that created the id. The node may be a MAC address.       |
| `3`     | `9073926b-929f-31c2-abc9-fad77ae3e8eb` | MD5 of a namespace and a name. Use when the same name must always produce the same id.                         |
| `4`     | `225b1555-69c6-4d7c-84e0-b71f52d070d1` | Random bits, with no time or host. Use as the default when the id only has to be unique.                       |
| `5`     | `cfbff0d1-9375-5685-968c-48ce8b15ae17` | SHA-1 of a namespace and a name. Use for the same stable ids as version 3, with SHA-1.                         |
| `6`     | `1f1c2f2a-28f7-667c-9234-001122334455` | Version 1 time and node, reordered so the values sort. Use when those ids should be stored in creation order.  |
| `7`     | `01a11aa3-322a-75c6-b387-783eed46490c` | Unix time in milliseconds, then random bits. Use for sortable ids that do not reveal a machine address.        |
| `8`     | `00001234-5678-8ef0-8000-000011223344` | Your own 48, 12, and 62 bit blocks. Use for a private layout that still has to be a valid UUID.                |

Versions 3 and 5 use the DNS namespace and the name `example.com`.
Versions 1 and 6 share the placeholder node `00:11:22:33:44:55`.
Version 8 is `a=0x12345678`, `b=0x9abcdef0`, `c=0x11223344`.
Versions 4 and 7 are single samples. Another call will differ.

## Library

`generate_uuid` takes one config mapping and can format the result.
`create_uuid` takes arguments and returns the raw UUID. Version 8
blocks are `a`, `b`, and `c` either way, the same values as
`uuid.uuid8(a, b, c)`.

### Generate UUID

```python
import uuid

from lupaxa.uuid_generator import UUIDGenerator

UUIDGenerator.generate_uuid()
UUIDGenerator.generate_uuid({"version": 1})
UUIDGenerator.generate_uuid({"version": 6})
UUIDGenerator.generate_uuid({"version": 7})
UUIDGenerator.generate_uuid(
    {"version": 8, "a": 0x12345678, "b": 0x9ABCDEF0, "c": 0x11223344}
)
UUIDGenerator.generate_uuid(
    {
        "version": 5,
        "namespace": uuid.NAMESPACE_DNS,
        "name": "example.com",
        "format_type": "uppercase",
        "prefix": "id-",
    }
)
```

### Create UUID

```python
import uuid

from lupaxa.uuid_generator import UUIDGenerator

UUIDGenerator.create_uuid()
UUIDGenerator.create_uuid(1)
UUIDGenerator.create_uuid(3, uuid.NAMESPACE_DNS, "example.com")
UUIDGenerator.create_uuid(5, uuid.NAMESPACE_DNS, "example.com")
UUIDGenerator.create_uuid(6)
UUIDGenerator.create_uuid(7)
UUIDGenerator.create_uuid(8, a=0x12345678, b=0x9ABCDEF0, c=0x11223344)
```

| Key                | Meaning                                                     |
| ------------------ | ----------------------------------------------------------- |
| `version`          | `1`, `3`, `4`, `5`, `6`, `7`, or `8`. Default is `4`        |
| `a`                | Version 8 block, 48 bits. Same as `uuid.uuid8`              |
| `b`                | Version 8 block, 12 bits. Extra high bits are ignored       |
| `c`                | Version 8 block, 62 bits. Omitted blocks are random         |
| `namespace`        | `uuid.UUID`. Required for versions 3 and 5                  |
| `name`             | String mixed into versions 3 and 5                          |
| `format_type`      | `standard`, `uppercase`, `lowercase`, or `no-dashes`        |
| `separator`        | Replacement for `-`. Default is `-`                         |
| `length`           | Keep this many characters after formatting                  |
| `prefix`           | Text placed before the identifier                           |
| `suffix`           | Text placed after the identifier                            |
| `custom_char_set`  | Alphabet for a non-UUID identifier. Requires `length`       |

Version 6 reorders the version 1 timestamp so values sort, and keeps
that same clock sequence and node. Version 7 needs no namespace. Its
first 48 bits are Unix time in milliseconds, so values from one process
sort by creation time. Version 8 uses the same `a`, `b`, and `c`
blocks as `uuid.uuid8`: 48, 12, and 62 bits. Wider integers keep
their low bits. An omitted block is filled at random.

`apply_format` and `add_prefix_suffix` are the steps `generate_uuid`
runs after `create_uuid`.
`encode_uuid` and `decode_uuid` use URL-safe Base64. `hash_uuid`
accepts `sha256` (default) or `md5`. `generate_unique_uuid` retries
until the value is absent from the list you pass.

```python
from lupaxa.uuid_generator import UUIDGenerator, UUIDGeneratorError

try:
    UUIDGenerator.generate_uuid({"version": 5})
except UUIDGeneratorError as exc:
    print(exc)
```

`UUIDGeneratorError` is a `ValueError`.

## CLI

```bash
uuid-generator
uuid-generator -n 3
uuid-generator --uuid-version 1
uuid-generator --uuid-version 6
uuid-generator --uuid-version 7
uuid-generator --uuid-version 8 --a 0x12345678 --b 0x9abcdef0 --c 0x11223344
uuid-generator --base64
uuid-generator --md5
uuid-generator --base64 --md5
uuid-generator --uuid-version 5 --namespace dns --name example.com
uuid-generator --format no-dashes --prefix id-
uuid-generator --version
```

One identifier is printed per line. The default is a single version 4 UUID.

| Flag             | Meaning                                              |
| ---------------- | ---------------------------------------------------- |
| `-n`, `--count`  | How many to print. Default is `1`                    |
| `--uuid-version` | `1`, `3`, `4`, `5`, `6`, `7`, or `8`. Default is `4` |
| `--a`            | Version 8 block `a`, 48 bits. Hex with `0x` is fine  |
| `--b`            | Version 8 block `b`, 12 bits                         |
| `--c`            | Version 8 block `c`, 62 bits                         |
| `--namespace`    | `dns`, `url`, `oid`, `x500`, or a UUID. Versions 3/5 |
| `--name`         | Name for versions 3 and 5                            |
| `--format`       | `standard`, `uppercase`, `lowercase`, or `no-dashes` |
| `--separator`    | Replacement for `-`                                  |
| `--length`       | Keep the first N characters                          |
| `--prefix`       | Text before each identifier                          |
| `--suffix`       | Text after each identifier                           |
| `--base64`       | URL-safe Base64 of each UUID, padding stripped       |
| `--md5`          | MD5 hex digest of each UUID string                   |
| `--version`      | Print `uuid-generator x.y.z` and exit `0`            |
| `--help`         | Show argparse help                                   |

| Result                         | Stdout                  | Exit |
| ------------------------------ | ----------------------- | ---- |
| Success                        | One identifier per line | `0`  |
| `--version`                    | `uuid-generator x.y.z`  | `0`  |
| Bad count, namespace, or flags | error on stderr         | `2`  |

`--base64` and `--md5` both describe the identifier that would have
been printed. Together they print the Base64 form, a space, then the
MD5 digest. `--base64` needs a value `uuid.UUID` can parse, so a
prefix, suffix, custom separator, or shortened length exits `2`.
Custom alphabets stay on the library.

## Development

```bash
make init
make python-install-dev
make python-check
```

<a href="https://github.com/the-lupaxa-project">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>

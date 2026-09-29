"""Builds sample repositories for trying adrpy-tui by hand, and for tests.

    python scripts/make_sample_repo.py <folder> [--language pt-br] [--extra N] [--reset]

Creates, under <folder>:
- sample/  decisions in every state (one in a subfolder), and decision-log
           entries; `--extra N`
           adds N more, in turn Proposed, Accepted and Rejected, for
           lists of several pages;
- legacy/  hand-written decision files with no header, for `migrate`;
- broken/  two files with the same number, for `check`;
- empty/   a folder with no .adrpy.json, for `init`.

Every decision and log entry is written by adrpy's own commands, so the
files are always what adrpy writes; only legacy/'s files and broken/'s copy
are written here, since they stand for what adrpy never writes.

<folder> must be empty, or be one this script built (it leaves a marker
file there): `--reset` deletes such a folder's content and builds it again,
and refuses any folder without the marker.
"""

import argparse
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

from adrpy_tui.core.client import Client

MARKER = ".adrpy-tui-samples"

LEGACY_FILES = {
    "0001-use-postgres.md": "# Use PostgreSQL\n\nWe store orders in PostgreSQL.\n",
    "0002-adopt-kafka.md": "# Adopt Kafka\n\nEvents go through Kafka.\n",
    "0003-drop-soap.md": "# Drop SOAP\n\nNew services expose REST only.\n",
}


# (scope, domain) of the extra decisions, in turn.
EXTRA_TOPICS = (("backend", "dados"), ("frontend", "ui"), ("security", "seguranca"), ("packaging", "distribuicao"))
# Well before the fixed decisions' dates, one day apart.
EXTRA_START = date(2025, 1, 1)


class SampleError(Exception):
    pass


def _run(client, command, *flags):
    result = client.run(command, flags)
    if not result.success:
        raise SampleError(f"adrpy {command} failed: {result.code}: {result.detail}")
    return result.data


def _new(client, repo, title, scope, domain, refdate):
    return _run(client, "new", "--path", str(repo), "--title", title, "--scope", scope, "--domain", domain,
                "--refdate", refdate)["created"]


def build_sample(client, repo, language):
    """Decisions in every state a command can take, with scopes and domains
    repeated for the suggestions, and three decision-log entries."""
    repo.mkdir(parents=True)
    init = client.run("init", ("--path", str(repo), "--language", language))
    if not init.success and init.code == "usage-error":
        # This machine has an install-level config, which --language can't
        # be combined with: the labels are that config's.
        print(f"note: {init.detail}", file=sys.stderr)
        init = client.run("init", ("--path", str(repo)))
    if not init.success:
        raise SampleError(f"adrpy init failed: {init.code}: {init.detail}")
    _run(client, "config", "--path", str(repo), "--lenrevision", "2")

    _new(client, repo, "Usar PostgreSQL", "backend", "dados", "2026-01-05")                          # Proposed
    accepted = _new(client, repo, "Adotar Textual", "frontend", "ui", "2026-01-06")
    _run(client, "approve", "--file", accepted, "--refdate", "2026-01-10")                          # Accepted
    rejected = _new(client, repo, "Usar MongoDB", "backend", "dados", "2026-01-07")
    _run(client, "reject", "--file", rejected, "--refdate", "2026-01-11")                           # Rejected
    # adrpy finds decisions in subfolders of the decisions folder too: one
    # lives in backend/, for explore's folder column and select.
    subfolder = Path(rejected).parent / "backend"
    subfolder.mkdir()
    Path(rejected).rename(subfolder / Path(rejected).name)
    old = _new(client, repo, "Autenticar com sessões", "security", "seguranca", "2026-01-08")
    _run(client, "approve", "--file", old, "--refdate", "2026-01-12")
    _run(client, "supersede", "--file", old, "--title", "Autenticar com OAuth", "--refdate", "2026-02-01")
    # ^ Superseded, and its successor Proposed
    revised = _new(client, repo, "Registrar em JSON", "backend", "observabilidade", "2026-01-09")
    _run(client, "approve", "--file", revised, "--refdate", "2026-01-13")
    _run(client, "revise", "--file", revised, "--refdate", "2026-02-02")                            # R01 Proposed
    versioned = _new(client, repo, "Publicar no PyPI", "packaging", "distribuicao", "2026-01-10")
    _run(client, "approve", "--file", versioned, "--refdate", "2026-01-14")
    _run(client, "version", "--file", versioned, "--refdate", "2026-02-03")                         # V02 Proposed

    path = ("--path", str(repo))
    _run(client, "log", *path, "--classification", "scope-note", "--scope", "backend", "--slug", "escopo-inicial",
         "--summary", "Escopo inicial do backend", "--body", "Entrada de exemplo.", "--refdate", "2026-02-04")
    _run(client, "log", *path, "--classification", "audit-finding", "--scope", "security", "--slug", "sessao-sem-expiracao",
         "--summary", "Sessões sem expiração", "--body", "Entrada de exemplo.", "--front", "stability",
         "--severity", "High", "--resolution", "Direct", "--refdate", "2026-02-05")
    _run(client, "log", *path, "--classification", "deferred", "--scope", "packaging", "--slug", "publicacao-adiada",
         "--summary", "Publicação adiada", "--body", "Entrada de exemplo.",
         "--reopenwhen", "adrpy-ai estar no PyPI", "--refdate", "2026-02-06")


def add_extra(client, repo, count):
    """`count` more decisions, in turn Proposed, Accepted and Rejected."""
    for n in range(count):
        scope, domain = EXTRA_TOPICS[n % len(EXTRA_TOPICS)]
        created = EXTRA_START + timedelta(days=2 * n)
        decision = _new(client, repo, f"Decisao de exemplo {n + 1:03}", scope, domain, created.isoformat())
        changed = (created + timedelta(days=1)).isoformat()
        if n % 3 == 1:
            _run(client, "approve", "--file", decision, "--refdate", changed)
        elif n % 3 == 2:
            _run(client, "reject", "--file", decision, "--refdate", changed)


def build_legacy(client, repo):
    """A repository whose decisions predate adrpy: no header, legacy names."""
    repo.mkdir(parents=True)
    _run(client, "init", "--path", str(repo))
    folder = repo / "doc" / "adr"
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in LEGACY_FILES.items():
        (folder / name).write_text(content, encoding="utf-8")


def build_broken(client, repo, language):
    """A repository `check` refuses: a decision copied by hand under another
    title keeps its number, as a merge of two branches can leave it."""
    repo.mkdir(parents=True)
    init = client.run("init", ("--path", str(repo), "--language", language))
    if not init.success:
        _run(client, "init", "--path", str(repo))
    first = Path(_new(client, repo, "Usar PostgreSQL", "backend", "dados", "2026-01-05"))
    _new(client, repo, "Adotar Textual", "frontend", "ui", "2026-01-06")
    shutil.copyfile(first, first.with_name(first.name.replace("usar-postgre-sql", "usar-mysql")))


def build(root, language="pt-br", reset=False, client=None, extra=0):
    root = Path(root)
    client = client or Client()
    if extra < 0:
        raise SampleError("--extra cannot be negative.")
    if root.exists() and any(root.iterdir()):
        if not reset:
            raise SampleError(f"{root} is not empty; use --reset to rebuild a folder this script built.")
        if not (root / MARKER).is_file():
            raise SampleError(f"{root} was not built by this script (no {MARKER}); nothing was deleted.")
        for entry in root.iterdir():
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
    root.mkdir(parents=True, exist_ok=True)
    (root / MARKER).write_text("Built by adrpy-tui's scripts/make_sample_repo.py; --reset may delete this folder's content.\n",
                               encoding="utf-8")
    build_sample(client, root / "sample", language)
    add_extra(client, root / "sample", extra)
    build_legacy(client, root / "legacy")
    build_broken(client, root / "broken", language)
    (root / "empty").mkdir()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Builds sample repositories for adrpy-tui.")
    parser.add_argument("folder")
    parser.add_argument("--language", default="pt-br", help="labels of the sample repository (default: pt-br)")
    parser.add_argument("--extra", type=int, default=0, metavar="N",
                        help="N more decisions in sample/, for lists of several pages (default: 0)")
    parser.add_argument("--reset", action="store_true", help="delete and rebuild a folder this script built")
    args = parser.parse_args(argv)
    try:
        build(args.folder, args.language, args.reset, extra=args.extra)
    except SampleError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    root = Path(args.folder).resolve()
    print(f"Built {root}:")
    for name in ("sample", "legacy", "broken", "empty"):
        print(f"  adrpy-tui --path {root / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

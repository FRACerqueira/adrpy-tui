"""What the TUI reads or lists from a repository, and the paths a person
gives it (ADR0006V02). Nothing here follows a folder link, resolves a path
with one on the way (resolving opens the target, which may be on another
machine), reads more of a file than is shown, or raises on a path that
cannot be looked at: such a path is simply not available."""

import codecs
import os
import stat
from pathlib import Path, PurePath


# The reparse points that lead elsewhere: a symlink, a junction (mount
# point) and a WSL symlink. Any other tag -- a OneDrive placeholder, a
# deduplicated file, an app execution alias -- is the file itself.
_LINK_TAGS = (0xA000000C, 0xA0000003, 0xA000001D)



def same_name(name, *names):
    """Whether `name` is one of `names` as this system compares file names
    (case-blind on Windows), as adrpy compares them."""
    return os.path.normcase(name) in {os.path.normcase(other) for other in names}

def _is_link(status):
    if stat.S_ISLNK(status.st_mode):
        return True
    reparse = getattr(status, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    return bool(reparse) and getattr(status, "st_reparse_tag", 0) in _LINK_TAGS


def outside_reason(root, path):
    """None when `path` lies inside the repository `root` with no folder
    link on the way -- a symlink or a Windows junction may lead anywhere;
    "link" when one is on the way; "outside" otherwise. Lexical first, so
    nothing outside the repository (a network path) is touched; then each
    component below the root is looked at with lstat. A component that is
    not there has nothing to follow; one that cannot be looked at (access
    denied) is not inside."""
    root = os.path.normpath(os.path.abspath(root))
    target = os.path.normpath(os.path.abspath(path))
    try:
        if os.path.commonpath([root, target]) != root:
            return "outside"
    except ValueError:  # another drive
        return "outside"
    current = root
    for part in PurePath(os.path.relpath(target, root)).parts:
        current = os.path.join(current, part)
        try:
            status = os.lstat(current)
        except (FileNotFoundError, NotADirectoryError):
            return None
        except (OSError, ValueError):
            return "outside"
        if _is_link(status):
            return "link"
    return None


def inside_repository(root, path):
    """Whether `path` lies inside the repository `root` with no folder link
    on the way (outside_reason)."""
    return outside_reason(root, path) is None


def repository_folder(root, relative):
    """(the folder a config setting names, spelled as adrpy resolves it --
    case, Windows' trailing dots --, and outside_reason's answer for it).
    Resolved only with no folder link on the way, where resolving opens
    nothing else."""
    folder = Path(os.path.abspath(os.path.normpath(Path(root) / relative)))
    reason = outside_reason(root, folder)
    return (folder.resolve() if reason is None else folder), reason


def is_dir(path):
    """Whether `path` is a folder; False when it cannot be looked at."""
    try:
        return Path(path).is_dir()
    except (OSError, ValueError):
        return False


def is_file(path):
    """Whether `path` is a file; False when it cannot be looked at."""
    try:
        return Path(path).is_file()
    except (OSError, ValueError):
        return False


def markdown_files(folder, recursive=True, unreadable=None):
    """The .md files under `folder`, sorted, never entering a folder link
    (a junction to a parent would never end); `.md` compared as adrpy's scan
    compares it (os.path.normcase). A folder that cannot be read lists
    nothing, and is added to `unreadable` when given."""
    found = []

    def failed(error):
        if unreadable is not None:
            unreadable.append(Path(error.filename))

    for top, folders, names in os.walk(folder, onerror=failed):
        if recursive:
            kept = []
            for name in folders:
                try:
                    if not _is_link(os.lstat(os.path.join(top, name))):
                        kept.append(name)
                except OSError:
                    pass
            folders[:] = kept
        else:
            folders[:] = []
        found += [Path(top) / name for name in names if os.path.normcase(name).endswith(".md")]
    return sorted(found)


def read_start(path, lines, characters):
    """(the file's first `lines` lines, at most `characters` of them, its
    total lines, its total characters). Only that start is kept; the rest is
    counted as it streams by, never held."""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    kept, kept_size, total, breaks, open_line, after_cr = [], 0, 0, 0, False, False
    with open(path, "rb") as source:
        while True:
            chunk = source.read(1 << 20)
            text = decoder.decode(chunk, final=not chunk)
            if text:
                total += len(text)
                # Line breaks as splitlines cuts them (CR, LF, CRLF, U+2028...),
                # a CRLF split across two chunks counted once.
                pieces = (text[1:] if after_cr and text[0] == "\n" else text).splitlines(keepends=True)
                breaks += sum(1 for piece in pieces if piece.splitlines()[0] != piece)
                if pieces:
                    open_line = pieces[-1].splitlines()[0] == pieces[-1]
                after_cr = text[-1] == "\r"
                # Kept until either limit is reached: past it, nothing more is shown.
                if kept_size <= characters and len("".join(kept).splitlines()) <= lines:
                    kept.append(text)
                    kept_size += len(text)
            if not chunk:
                break
    start = "".join((("".join(kept)).splitlines(keepends=True))[:lines])[:characters]
    return start, breaks + (1 if open_line else 0), total

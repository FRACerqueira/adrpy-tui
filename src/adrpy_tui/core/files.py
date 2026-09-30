"""What the TUI reads or lists from a repository, and the paths a person
gives it (ADR0006V02). Nothing here follows a folder link, resolves a path
(resolving opens the target, which may be on another machine), reads more
of a file than is shown, or raises on a path that cannot be looked at: such
a path is simply not available."""

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


def inside_repository(root, path):
    """Whether `path` lies inside the repository `root` with no folder link
    on the way -- a symlink or a Windows junction may lead anywhere. Lexical
    first, so nothing outside the repository (a network path) is touched;
    then each component below the root is looked at with lstat. A component
    that is not there has nothing to follow; one that cannot be looked at
    (access denied) is not inside."""
    root = os.path.normpath(os.path.abspath(root))
    target = os.path.normpath(os.path.abspath(path))
    try:
        if os.path.commonpath([root, target]) != root:
            return False
    except ValueError:  # another drive
        return False
    current = root
    for part in PurePath(os.path.relpath(target, root)).parts:
        current = os.path.join(current, part)
        try:
            status = os.lstat(current)
        except (FileNotFoundError, NotADirectoryError):
            return True
        except (OSError, ValueError):
            return False
        if _is_link(status):
            return False
    return True


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


def markdown_files(folder, recursive=True):
    """The .md files under `folder`, sorted, never entering a folder link
    (a junction to a parent would never end); a folder that cannot be read
    lists nothing."""
    found = []
    for top, folders, names in os.walk(folder, onerror=lambda error: None):
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
        found += [Path(top) / name for name in names if name.lower().endswith(".md")]
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

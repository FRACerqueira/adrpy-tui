"""The check for a newer adrpy-tui on PyPI, with the standard library only
(ADR0008V01): the versions published, and the newest one above the
installed version."""

import http.client
import json
import time
import urllib.request

from adrpy_tui.core.text import visible
from adrpy_tui.core.versions import order

URL = "https://pypi.org/pypi/adrpy-tui/json"
TIMEOUT = 5  # seconds, for each read of the socket
# Seconds for the whole answer: TIMEOUT alone lets a byte every few seconds go on for the whole run.
DEADLINE = 15
# The answer is a few kilobytes per release: more than this is not PyPI's.
LIMIT = 4 * 1024 * 1024
# Everything published() raises for no network or an answer that cannot be read.
CHECK_ERRORS = (OSError, http.client.HTTPException, ValueError, RecursionError, TypeError, AttributeError, KeyError)


def _open(url, timeout):
    return urllib.request.urlopen(url, timeout=timeout)  # noqa: S310 -- a fixed https URL


def published():
    """The versions on PyPI with at least one file not yanked; raises one of
    CHECK_ERRORS when PyPI can't be reached or its answer can't be read."""
    deadline = time.monotonic() + DEADLINE
    raw = b""
    with _open(URL, TIMEOUT) as response:
        while chunk := response.read1(64 * 1024):
            raw += chunk
            if len(raw) > LIMIT:
                raise ValueError("answer too large")
            if time.monotonic() > deadline:
                raise TimeoutError("answer too slow")
    releases = json.loads(raw.decode("utf-8"))["releases"]
    if not isinstance(releases, dict):
        raise TypeError("releases is not an object")
    found = []
    for version, files in releases.items():
        if not isinstance(files, list) or not all(isinstance(file, dict) for file in files):
            raise TypeError("a release's files are not a list of objects")
        if any(not file.get("yanked", False) for file in files):
            found.append(version)
    return found


def newer(installed, versions, prereleases):
    """The newest of `versions` above `installed`, as said on screen, or None.
    Development builds are never offered; pre-releases only when asked for.
    A version that is not PEP 440's is skipped, and so is an installed one."""
    try:
        floor = order(installed)
    except ValueError:
        return None
    best = None
    for version in versions:
        try:
            key = order(version)
        except ValueError:
            continue
        release, stage, _post, dev = key
        if dev != float("inf") or (stage[0] < 3 and not prereleases):
            continue
        if key > floor and (best is None or key > best[0]):
            best = (key, version)
    return visible(best[1]) if best else None

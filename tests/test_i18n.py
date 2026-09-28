import re
import string
from importlib import resources

import pytest

from adrpy_tui.core import i18n


def _pack(language):
    import json

    return json.loads(
        resources.files("adrpy_tui.resources.language_packs").joinpath(f"{language}.json").read_text(encoding="utf-8")
    )


def _placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_the_packs_are_the_languages_adrpy_supports(client):
    """ADR005V01: the same list as `adrpy help init`'s --language."""
    contract = client.run("help", ("init",)).data["commands"][0]
    [language] = [argument for argument in contract["arguments"] if argument["name"] == "language"]
    adrpy_languages = re.search(r"\(([^)]*)\)", language["description"]).group(1)
    assert set(re.findall(r"'([a-z]{2}-[a-z]{2})'", adrpy_languages)) == set(i18n.LANGUAGES)

    shipped = {entry.name.removesuffix(".json") for entry in resources.files("adrpy_tui.resources.language_packs").iterdir()
               if entry.name.endswith(".json")}
    assert shipped == set(i18n.LANGUAGES)


@pytest.mark.parametrize("language", i18n.LANGUAGES)
def test_every_pack_has_exactly_the_reference_keys_and_placeholders(language):
    reference, pack = _pack(i18n.DEFAULT_LANGUAGE), _pack(language)
    assert pack.keys() == reference.keys()
    for key, text in reference.items():
        assert _placeholders(pack[key]) == _placeholders(text), key
        assert pack[key].strip(), key


@pytest.mark.parametrize("name, expected", [
    ("pt_BR.UTF-8", "pt-br"),
    ("pt-BR", "pt-br"),
    ("pt_PT", "pt-br"),
    ("en_GB", "en-us"),
    ("nl_NL", "nl-be"),
    ("C", None),
    ("sv_SE", None),
    ("", None),
    (None, None),
])
def test_match_language(name, expected):
    assert i18n.match_language(name) == expected

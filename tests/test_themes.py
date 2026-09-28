import pytest
from textual.color import Color

from adrpy_tui.core import themes


@pytest.mark.parametrize("preset", themes.PRESETS)
def test_every_preset_colors_every_role_with_a_valid_color(preset):
    colors = themes.PRESETS[preset]["colors"]
    assert set(colors) == set(themes.ROLES)
    for role, value in colors.items():
        Color.parse(value)  # raises on an invalid color


WCAG_AA = 4.5  # minimum contrast ratio for normal text


def _luminance(color):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = color.rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast(first, second):
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _backgrounds():
    """Each base theme's own background, as Textual computes it."""
    import asyncio

    from textual.app import App

    found = {}

    async def main():
        app = App()
        async with app.run_test():
            for base in {spec["base"] for spec in themes.PRESETS.values()}:
                app.theme = base
                found[base] = Color.parse(app.get_css_variables()["background"])

    asyncio.run(main())
    return found


@pytest.mark.parametrize("preset", themes.PRESETS)
def test_every_text_role_meets_wcag_aa_contrast_on_its_background(preset):
    """Text roles against the screen; tui-cursor is the highlighted item's
    background, checked against its own text below."""
    colors = themes.PRESETS[preset]["colors"]
    background = _backgrounds()[themes.PRESETS[preset]["base"]]
    too_low = {
        role: round(_contrast(Color.parse(value), background), 2)
        for role, value in colors.items()
        if role != "tui-cursor" and _contrast(Color.parse(value), background) < WCAG_AA
    }
    assert too_low == {}


@pytest.mark.parametrize("preset", themes.PRESETS)
def test_the_highlighted_item_meets_wcag_aa_contrast_on_the_cursor(preset):
    colors = themes.PRESETS[preset]["colors"]
    assert _contrast(Color.parse(colors["tui-highlight"]), Color.parse(colors["tui-cursor"])) >= WCAG_AA


def test_the_default_preset_is_the_original_palette():
    assert themes.PRESETS[themes.DEFAULT_PRESET]["colors"]["tui-banner"] == "#FF8C00"


def test_an_unknown_preset_falls_back_to_the_default():
    assert themes.preset_or_default("from-a-newer-version") == themes.DEFAULT_PRESET
    assert themes.preset_or_default(None) == themes.DEFAULT_PRESET
    assert themes.preset_or_default("light") == "light"

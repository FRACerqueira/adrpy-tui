"""WCAG contrast between two colors, as (red, green, blue) from 0 to 255."""

WCAG_AA = 4.5  # the minimum for normal text


def _luminance(rgb):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def ratio(first, second):
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def readable_on(rgb):
    """Black or white, whichever reads better on `rgb` -- by contrast, not
    by brightness as Textual's "auto" picks (3.48:1 white on #00A000)."""
    return "#000000" if ratio((0, 0, 0), rgb) >= ratio((255, 255, 255), rgb) else "#FFFFFF"

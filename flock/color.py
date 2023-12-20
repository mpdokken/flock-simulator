from typing import TypeAlias

ColorType: TypeAlias = tuple[int, int, int]


def lighten(color: ColorType, scale: float = 1.0) -> ColorType:
    """Lighten the input color."""

    min_gap = min(255 - color[i] for i in range(3))
    additional = min_gap * scale
    return tuple(min(int(val + additional), 255) for val in color)

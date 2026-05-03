'''Navigation algebra over cube stickers.'''

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum, auto
from typing import cast

from .model import Color, CornerSticker, Cube, EdgeSticker, Side, Sticker, solved

class Nav(Enum):
  '''Navigation steps: next or other.'''
  NEXT = auto()
  OTHER = auto()

def nav(steps: Iterable[Nav], cube: Cube, sticker: Sticker) -> Sticker:
  '''Apply a sequence of navigation steps.'''
  current: Sticker = sticker
  is_edge: bool = isinstance(current, EdgeSticker)
  step: Nav
  for step in steps:
    match step:
      case Nav.NEXT:
        if is_edge:
          current = cube.next_corner[cast(EdgeSticker, current)]
        else:
          current = cube.next_edge[cast(CornerSticker, current)]
        is_edge = not is_edge
      case Nav.OTHER:
        current = current.other
  return current

def nav_cc(
  steps: Iterable[Nav], cube: Cube, sticker: CornerSticker
) -> CornerSticker:
  '''Navigate corner to corner under even NEXT parity.'''
  return cast(CornerSticker, nav(steps, cube, sticker))

def parse_navs(text: str) -> list[Nav]:
  '''Parse a string of N and O into navigation steps.'''
  result: list[Nav] = []
  ch: str
  for ch in text:
    match ch:
      case 'N':
        result.append(Nav.NEXT)
      case 'O':
        result.append(Nav.OTHER)
      case _:
        raise ValueError(f'invalid nav character: {ch!r}')
  return result

HOME_TO_SIDE: dict[Side, list[Nav]] = {
  Side.FRONT: parse_navs(''),
  Side.TOP: parse_navs('OO'),
  Side.RIGHT: parse_navs('NNOO'),
  Side.LEFT: parse_navs('O'),
  Side.BOTTOM: parse_navs('ONNOO'),
  Side.BACK: parse_navs('OONNOO'),
}

def corner_on_side(cube: Cube, side: Side) -> CornerSticker:
  '''Return a representative corner sticker for a side.'''
  return nav_cc(HOME_TO_SIDE[side], cube, cube.home)

def side_corners(
  cube: Cube, start: CornerSticker
) -> list[CornerSticker]:
  '''Return the four corners on the same side.'''
  result: list[CornerSticker] = [start]
  current: CornerSticker = start
  for _ in range(3):
    edge: EdgeSticker = cube.next_edge[current]
    current = cube.next_corner[edge]
    result.append(current)
  return result

def sticker_side(cube: Cube, sticker: Sticker) -> Side:
  '''Return the side containing the given sticker.'''
  corner: CornerSticker
  if isinstance(sticker, EdgeSticker):
    corner = cube.next_corner[sticker]
  else:
    corner = cast(CornerSticker, sticker)
  corners: list[CornerSticker] = side_corners(cube, corner)
  side: Side
  path: list[Nav]
  for side, path in HOME_TO_SIDE.items():
    home_corner: CornerSticker = nav_cc(path, cube, cube.home)
    if home_corner in corners:
      return side
  raise ValueError('sticker not found on any side')

# --- precompute orientation tables ---

_temp: Cube = solved()

side_colors: dict[tuple[Color, Color, Side], Color] = {}

corner: CornerSticker
for corner in _temp.next_edge.keys():
  s: CornerSticker = corner
  for _ in range(3):
    side: Side
    path: list[Nav]
    for side, path in HOME_TO_SIDE.items():
      target: CornerSticker = nav_cc(path, _temp, s)
      side_colors[(s.color, s.other.other.color, side)] = target.color
    s = s.other

color_sides: dict[tuple[Color, Color, Color], Side] = {
  (a, b, c): side
  for (a, b, side), c in side_colors.items()
}

del _temp

def side_color(cube: Cube, side: Side) -> Color:
  '''Return the color of a side.'''
  return side_colors[(cube.front_color, cube.top_color, side)]

def color_side(cube: Cube, color: Color) -> Side:
  '''Return the side corresponding to a color.'''
  return color_sides[(cube.front_color, cube.top_color, color)]

def all_colors(cube: Cube) -> dict[Side, list[Color]]:
  '''Return the eight sticker colors on each side.'''
  result: dict[Side, list[Color]] = {}
  side: Side
  for side in Side:
    st: Sticker = corner_on_side(cube, side)
    colors: list[Color] = []
    for _ in range(8):
      colors.append(st.color)
      st = nav([Nav.NEXT], cube, st)
    result[side] = colors
  return result

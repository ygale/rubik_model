'''Reachability test for the Rubik's cube.

A cube position is reachable from the solved position by face moves
if and only if the three criteria checked here are all satisfied.
'''

from __future__ import annotations

from collections.abc import Iterator

from .model import (
  Color,
  CornerSticker,
  Cube,
  EdgeSticker,
  Side,
  solved,
)
from .navigation import (
  corner_on_side,
  side_color,
  side_corners,
  sticker_side,
)
from .utils import even_permutation

_PRIORITY: list[Color] = [
  Color.BLUE, Color.GREEN, Color.WHITE, Color.YELLOW,
]

_WY: frozenset[Color] = frozenset({Color.WHITE, Color.YELLOW})

type _Cubie3 = frozenset[Color]
type _Cubie2 = frozenset[Color]

def _all_corners(cube: Cube) -> Iterator[CornerSticker]:
  '''Yield one sticker per corner cubie via navigation.

  Yields the 4 front-face corners followed by the 4 back-face corners.
  '''
  yield from side_corners(cube, cube.home)
  yield from side_corners(cube, corner_on_side(cube, Side.BACK))

def _all_edges(cube: Cube) -> Iterator[EdgeSticker]:
  '''Yield one sticker per edge cubie via navigation.

  For front-face corners: N gives the 4 front-ring edges,
  OON gives the 4 middle-layer edges.
  For back-face corners: N gives the 4 back-ring edges.
  '''
  front: list[CornerSticker] = side_corners(cube, cube.home)
  back: list[CornerSticker] = side_corners(
    cube, corner_on_side(cube, Side.BACK),
  )
  for c in front:
    yield cube.next_edge[c]
  for c in front:
    yield cube.next_edge[c.other.other]
  for c in back:
    yield cube.next_edge[c]

def _corner_cubie(cs: CornerSticker) -> _Cubie3:
  '''Return the frozenset of colors of a corner cubie.'''
  return frozenset({cs.color, cs.other.color, cs.other.other.color})

def _edge_cubie(es: EdgeSticker) -> _Cubie2:
  '''Return the frozenset of colors of an edge cubie.'''
  return frozenset({es.color, es.other.color})

_ref: Cube = solved()
_SOLVED_CORNERS: list[_Cubie3] = [
  _corner_cubie(cs) for cs in _all_corners(_ref)
]
_SOLVED_EDGES: list[_Cubie2] = [
  _edge_cubie(es) for es in _all_edges(_ref)
]

def locations_ok(cube: Cube) -> bool:
  '''Return True if corner and edge permutations have the same parity.'''
  corner_even: bool = even_permutation(
    [_corner_cubie(cs) for cs in _all_corners(cube)],
    _SOLVED_CORNERS,
  )
  edge_even: bool = even_permutation(
    [_edge_cubie(es) for es in _all_edges(cube)],
    _SOLVED_EDGES,
  )
  return corner_even == edge_even

def _rep_sticker(es: EdgeSticker) -> EdgeSticker:
  '''Return the representative sticker of an edge cubie.

  The representative sticker is the one whose color appears earliest
  in the priority order: blue, green, white, yellow.
  '''
  for color in _PRIORITY:
    if es.color == color:
      return es
    if es.other.color == color:
      return es.other
  raise ValueError(
    f'no priority color found in edge cubie: '
    f'{es.color}, {es.other.color}'
  )

def _rep_face(cube: Cube, es: EdgeSticker) -> Side:
  '''Return the representative face of an edge cubie.

  The representative face is the one of the two faces on which the
  cubie's stickers lie whose center color appears earliest in the
  priority order: blue, green, white, yellow.
  '''
  sides: list[Side] = [
    sticker_side(cube, es),
    sticker_side(cube, es.other),
  ]
  for color in _PRIORITY:
    for side in sides:
      if side_color(cube, side) == color:
        return side
  raise ValueError(
    f'no priority color found among faces of edge cubie: '
    f'{es.color}, {es.other.color}'
  )

def edge_flips_ok(cube: Cube) -> bool:
  '''Return True if the number of flipped edge cubies is even.

  An edge cubie is flipped if its representative sticker is not on
  its representative face.
  '''
  flipped: int = sum(
    1
    for es in _all_edges(cube)
    if sticker_side(cube, _rep_sticker(es)) != _rep_face(cube, es)
  )
  return flipped % 2 == 0

def _wy_sticker(cs: CornerSticker) -> CornerSticker:
  '''Return the white-or-yellow sticker of a corner cubie.'''
  s: CornerSticker = cs
  for _ in range(3):
    if s.color in _WY:
      return s
    s = s.other
  raise ValueError(
    f'no white/yellow sticker in corner cubie: '
    f'{cs.color}, {cs.other.color}, {cs.other.other.color}'
  )

def _corner_rotation(cube: Cube, cs: CornerSticker) -> int:
  '''Return the rotation number (0, 1, or 2) of a corner cubie.

  Let r be the white-or-yellow sticker of the cubie.
  If r is on a white/yellow face, rotation is 0.
  If r.other is on a white/yellow face, rotation is 1.
  Otherwise rotation is 2.
  '''
  r: CornerSticker = _wy_sticker(cs)
  if side_color(cube, sticker_side(cube, r)) in _WY:
    return 0
  if side_color(cube, sticker_side(cube, r.other)) in _WY:
    return 1
  return 2

def corner_rotations_ok(cube: Cube) -> bool:
  '''Return True if the sum of corner rotation numbers is divisible by 3.'''
  total: int = sum(
    _corner_rotation(cube, cs) for cs in _all_corners(cube)
  )
  return total % 3 == 0

def reachable(cube: Cube) -> bool:
  '''Return True if the cube is reachable from the solved position by moves.

  A cube is reachable if and only if:
  - corner and edge permutations have the same parity,
  - the number of flipped edge cubies is even, and
  - the sum of corner rotation numbers is divisible by three.
  '''
  return (
    locations_ok(cube)
    and edge_flips_ok(cube)
    and corner_rotations_ok(cube)
  )

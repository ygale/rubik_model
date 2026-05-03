'''Cube integrity checks, shared by test_model and test_move.'''

from __future__ import annotations

from rubik_cube_model import (
  Color,
  CornerSticker,
  Cube,
  EdgeSticker,
)
from rubik_cube_model.reachable import (
  corner_rotations_ok,
  edge_flips_ok,
  locations_ok,
  reachable,
)

_OPPOSITE_PAIRS: frozenset[frozenset[Color]] = frozenset({
  frozenset({Color.WHITE, Color.YELLOW}),
  frozenset({Color.RED, Color.ORANGE}),
  frozenset({Color.BLUE, Color.GREEN}),
})

def check_cube_integrity(cube: Cube) -> None:
  '''Assert all integrity invariants for a Cube.'''
  next_edge: dict[CornerSticker, EdgeSticker] = cube.next_edge
  next_corner: dict[EdgeSticker, CornerSticker] = cube.next_corner
  assert len(next_edge) == 24, (
    f'next_edge has {len(next_edge)} keys, expected 24'
  )
  assert len(next_corner) == 24, (
    f'next_corner has {len(next_corner)} keys, expected 24'
  )
  edge_values: list[EdgeSticker] = list(next_edge.values())
  assert len(set(edge_values)) == 24, (
    'next_edge values are not all distinct'
  )
  corner_values: list[CornerSticker] = list(next_corner.values())
  assert len(set(corner_values)) == 24, (
    'next_corner values are not all distinct'
  )
  for edge in edge_values:
    assert edge in next_corner, (
      'a value of next_edge is not a key in next_corner'
    )
  for corner in corner_values:
    assert corner in next_edge, (
      'a value of next_corner is not a key in next_edge'
    )
  for corner in next_edge:
    assert corner.other in next_edge, (
      'corner.other is not a key in next_edge'
    )
    assert corner.other.other in next_edge, (
      'corner.other.other is not a key in next_edge'
    )
  for edge in next_corner:
    assert edge.other in next_corner, (
      'edge.other is not a key in next_corner'
    )
  assert cube.home in next_edge, (
    'cube.home is not a key in next_edge'
  )
  assert (
    frozenset({cube.front_color, cube.top_color})
    not in _OPPOSITE_PAIRS
  ), (
    'front_color and top_color are opposite sides'
  )
  if not reachable(cube):
    assert locations_ok(cube), (
      'corner and edge permutations have different parity'
    )
    assert edge_flips_ok(cube), (
      'number of flipped edge cubies is odd'
    )
    assert corner_rotations_ok(cube), (
      'sum of corner rotation numbers is not divisible by 3'
    )

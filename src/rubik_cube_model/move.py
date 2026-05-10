'''Face moves implemented via local sticker cycles.'''

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .model import CornerSticker, Cube, EdgeSticker, Side, shallow_copy
from .navigation import (
  Nav,
  nav_cc,
  corner_on_side,
  side_corners,
  parse_navs,
)

class Multiplicity(Enum):
  '''Move multiplicity.'''
  CW = auto()
  CCW = auto()
  TWO = auto()


# Inverse multiplicity: CW<->CCW, TWO is self-inverse.
invert: dict[Multiplicity, Multiplicity] = {
    Multiplicity.CW:  Multiplicity.CCW,
    Multiplicity.CCW: Multiplicity.CW,
    Multiplicity.TWO: Multiplicity.TWO,
}

@dataclass(frozen=True)
class Move:
  '''A face move: a side and a multiplicity.'''
  face: Side
  mult: Multiplicity

restore_home: dict[tuple[Side, Multiplicity], list[Nav]] = {
  (Side.FRONT, Multiplicity.CW): parse_navs('ONNO'),
  (Side.FRONT, Multiplicity.CCW): parse_navs('NN'),
  (Side.FRONT, Multiplicity.TWO): parse_navs('NNNN'),

  (Side.LEFT, Multiplicity.CW): parse_navs('OONN'),
  (Side.LEFT, Multiplicity.CCW): parse_navs('OONNOO'),
  (Side.LEFT, Multiplicity.TWO): parse_navs('ONNNNOO'),

  (Side.TOP, Multiplicity.CW): parse_navs('NNOO'),
  (Side.TOP, Multiplicity.CCW): parse_navs('OONNO'),
  (Side.TOP, Multiplicity.TWO): parse_navs('OONNNNO'),
}

def _move_corner(
  cube: Cube, corner: CornerSticker, m: Multiplicity
) -> None:
  '''Rotate the face of a corner with given multiplicity.

  Note: caller may need to restore cube.home afterwards.
  '''
  corners: list[CornerSticker] = side_corners(cube, corner)

  corners_oo: list[CornerSticker] = [
    c.other.other for c in corners
  ]

  edges_no: list[EdgeSticker] = [
    cube.next_edge[c].other for c in corners_oo
  ]

  match m:
    case Multiplicity.CW:
      (
        cube.next_edge[corners_oo[0]],
        cube.next_edge[corners_oo[1]],
        cube.next_edge[corners_oo[2]],
        cube.next_edge[corners_oo[3]],
      ) = (
        cube.next_edge[corners_oo[1]],
        cube.next_edge[corners_oo[2]],
        cube.next_edge[corners_oo[3]],
        cube.next_edge[corners_oo[0]],
      )

      (
        cube.next_corner[edges_no[0]],
        cube.next_corner[edges_no[1]],
        cube.next_corner[edges_no[2]],
        cube.next_corner[edges_no[3]],
      ) = (
        cube.next_corner[edges_no[3]],
        cube.next_corner[edges_no[0]],
        cube.next_corner[edges_no[1]],
        cube.next_corner[edges_no[2]],
      )

    case Multiplicity.CCW:
      (
        cube.next_edge[corners_oo[0]],
        cube.next_edge[corners_oo[1]],
        cube.next_edge[corners_oo[2]],
        cube.next_edge[corners_oo[3]],
      ) = (
        cube.next_edge[corners_oo[3]],
        cube.next_edge[corners_oo[0]],
        cube.next_edge[corners_oo[1]],
        cube.next_edge[corners_oo[2]],
      )

      (
        cube.next_corner[edges_no[0]],
        cube.next_corner[edges_no[1]],
        cube.next_corner[edges_no[2]],
        cube.next_corner[edges_no[3]],
      ) = (
        cube.next_corner[edges_no[1]],
        cube.next_corner[edges_no[2]],
        cube.next_corner[edges_no[3]],
        cube.next_corner[edges_no[0]],
      )

    case Multiplicity.TWO:
      (
        cube.next_edge[corners_oo[0]],
        cube.next_edge[corners_oo[2]],
      ) = (
        cube.next_edge[corners_oo[2]],
        cube.next_edge[corners_oo[0]],
      )

      (
        cube.next_edge[corners_oo[1]],
        cube.next_edge[corners_oo[3]],
      ) = (
        cube.next_edge[corners_oo[3]],
        cube.next_edge[corners_oo[1]],
      )

      (
        cube.next_corner[edges_no[0]],
        cube.next_corner[edges_no[2]],
      ) = (
        cube.next_corner[edges_no[2]],
        cube.next_corner[edges_no[0]],
      )

      (
        cube.next_corner[edges_no[1]],
        cube.next_corner[edges_no[3]],
      ) = (
        cube.next_corner[edges_no[3]],
        cube.next_corner[edges_no[1]],
      )

def _move_home(cube: Cube, side: Side, m: Multiplicity) -> None:
  '''Restore home pointer after a face move.'''
  key: tuple[Side, Multiplicity] = (side, m)
  if key in restore_home:
    cube.home = nav_cc(restore_home[key], cube, cube.home)

def move(m: Move, cube: Cube) -> None:
  '''Rotate a face with given multiplicity.'''
  corner: CornerSticker = corner_on_side(cube, m.face)
  _move_corner(cube, corner, m.mult)
  _move_home(cube, m.face, m.mult)

def moved(m: Move, cube: Cube) -> Cube:
  '''Return a new cube after rotating a face.'''
  new: Cube = shallow_copy(cube)
  move(m, new)
  return new

'''Core cube model with minimal, link-based representation.'''

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, auto

class Color(Enum):
  '''Enumeration of the six cube colors.'''
  WHITE = auto()
  YELLOW = auto()
  RED = auto()
  ORANGE = auto()
  BLUE = auto()
  GREEN = auto()

class Side(Enum):
  '''Enumeration of the six cube sides.'''
  FRONT = auto()
  BACK = auto()
  LEFT = auto()
  RIGHT = auto()
  TOP = auto()
  BOTTOM = auto()

@dataclass(eq=False)
class Sticker(ABC):
  '''Abstract sticker with a color and cyclic partner.'''
  color: Color
  other: Sticker = field(init=False)

  def __post_init__(self) -> None:
    '''Initialize as a self-loop before wiring.'''
    self.other = self

  def __hash__(self) -> int:
    '''Use object identity for hashing.'''
    return id(self)

@dataclass(eq=False)
class CornerSticker(Sticker):
  '''Corner sticker linked in a 3-cycle.'''
  other: CornerSticker = field(init=False)

@dataclass(eq=False)
class EdgeSticker(Sticker):
  '''Edge sticker linked in a 2-cycle.'''
  other: EdgeSticker = field(init=False)

@dataclass(eq=False)
class Cube:
  '''Cube defined by one corner and cyclic adjacency maps.'''
  home: CornerSticker
  front_color: Color
  top_color: Color
  next_edge: dict[CornerSticker, EdgeSticker]
  next_corner: dict[EdgeSticker, CornerSticker]

def validate_links(cube: Cube) -> None:
  '''Check consistency between next_edge and next_corner.'''
  corner: CornerSticker
  edge: EdgeSticker
  for corner, edge in cube.next_edge.items():
    assert cube.next_corner[edge] is corner
  for edge, corner in cube.next_corner.items():
    assert cube.next_edge[corner] is edge

def solved() -> Cube:
  '''Construct a solved cube using local color relationships.'''
  FRONT: Color = Color.GREEN
  BACK: Color = Color.BLUE
  RIGHT: Color = Color.RED
  LEFT: Color = Color.ORANGE
  TOP: Color = Color.WHITE
  BOTTOM: Color = Color.YELLOW

  edge_cubies: dict[tuple[Color, Color], EdgeSticker] = {}

  def make_edge(a: Color, b: Color) -> None:
    '''Create one edge cubie with two directed stickers.'''
    s_ab: EdgeSticker = EdgeSticker(a)
    s_ba: EdgeSticker = EdgeSticker(b)
    s_ab.other = s_ba
    s_ba.other = s_ab
    edge_cubies[(a, b)] = s_ab
    edge_cubies[(b, a)] = s_ba

  make_edge(FRONT, TOP)
  make_edge(FRONT, RIGHT)
  make_edge(FRONT, BOTTOM)
  make_edge(FRONT, LEFT)
  make_edge(BACK, TOP)
  make_edge(BACK, RIGHT)
  make_edge(BACK, BOTTOM)
  make_edge(BACK, LEFT)
  make_edge(TOP, RIGHT)
  make_edge(TOP, LEFT)
  make_edge(BOTTOM, RIGHT)
  make_edge(BOTTOM, LEFT)

  next_edge: dict[CornerSticker, EdgeSticker] = {}
  next_corner: dict[EdgeSticker, CornerSticker] = {}

  def make_corner(a: Color, b: Color, c: Color) -> CornerSticker:
    '''Create one corner cubie and wire local adjacencies.'''
    s: tuple[CornerSticker, CornerSticker, CornerSticker] = (
      CornerSticker(a),
      CornerSticker(b),
      CornerSticker(c),
    )
    s[0].other = s[1]
    s[1].other = s[2]
    s[2].other = s[0]

    for i in range(3):
      curr: CornerSticker = s[i]
      nxt: CornerSticker = s[(i + 1) % 3]
      prv: CornerSticker = s[(i - 1) % 3]
      c0: Color = curr.color
      c1: Color = nxt.color
      c2: Color = prv.color
      next_edge[curr] = edge_cubies[(c0, c2)]
      next_corner[edge_cubies[(c0, c1)]] = curr
    return s[0]

  home: CornerSticker = make_corner(
              FRONT, LEFT, TOP)
  make_corner(FRONT, TOP, RIGHT)
  make_corner(FRONT, RIGHT, BOTTOM)
  make_corner(FRONT, BOTTOM, LEFT)
  make_corner(BACK, RIGHT, TOP)
  make_corner(BACK, BOTTOM, RIGHT)
  make_corner(BACK, LEFT, BOTTOM)
  make_corner(BACK, TOP, LEFT)

  return Cube(
    home=home,
    front_color=FRONT,
    top_color=TOP,
    next_edge=next_edge,
    next_corner=next_corner,
  )

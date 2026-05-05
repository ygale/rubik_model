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
  _hash: int = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    '''Initialize as a self-loop before wiring.'''
    self._rewire(self)

  def _rewire(self, other: Sticker) -> None:
    '''Set partner and recompute hash.'''
    self.other = other
    self._hash = hash((self.color, other.color))

  def __eq__(self, other: object) -> bool:
    '''Equality based on color pair.'''
    if not isinstance(other, Sticker):
      return NotImplemented
    return self.color == other.color and self.other.color == other.other.color

  def __hash__(self) -> int:
    '''Hash based on this sticker's color and its partner's color.'''
    return self._hash

@dataclass(eq=False)
class CornerSticker(Sticker):
  '''Corner sticker linked in a 3-cycle.'''
  other: CornerSticker = field(init=False)

@dataclass(eq=False)
class EdgeSticker(Sticker):
  '''Edge sticker linked in a 2-cycle.'''
  other: EdgeSticker = field(init=False)

@dataclass
class Cube:
  '''Cube defined by one corner and cyclic adjacency maps.'''
  home: CornerSticker
  front_color: Color
  top_color: Color
  next_edge: dict[CornerSticker, EdgeSticker]
  next_corner: dict[EdgeSticker, CornerSticker]

def shallow_copy(cube: Cube) -> Cube:
  '''Return a new Cube sharing all sticker objects but with new dicts.

  Moves only reassign dict values (which sticker a key maps to); they
  never mutate sticker objects themselves. A shallow copy therefore
  gives full independence between the two cubes without allocating new
  sticker objects.
  '''
  return Cube(
    home=cube.home,
    front_color=cube.front_color,
    top_color=cube.top_color,
    next_edge=dict(cube.next_edge),
    next_corner=dict(cube.next_corner),
  )

def solved(initial: Cube | None = None) -> Cube:
  '''Construct a solved cube.

  If initial is supplied, reuse its sticker objects instead of
  allocating new ones. Each directed sticker is uniquely identified
  by (sticker.color, sticker.other.color), so every sticker from
  initial is indexed by that pair and looked up in place of a freshly
  constructed one. Only new dicts are built; the sticker objects and
  their .other links are left untouched.
  '''
  color: dict[Side, Color] = {
    Side.FRONT:  Color.GREEN,
    Side.BACK:   Color.BLUE,
    Side.RIGHT:  Color.RED,
    Side.LEFT:   Color.ORANGE,
    Side.TOP:    Color.WHITE,
    Side.BOTTOM: Color.YELLOW,
  }

  existing_edges: dict[tuple[Color, Color], EdgeSticker]
  existing_corners: dict[tuple[Color, Color], CornerSticker]
  if initial is not None:
    existing_edges = {
      (es.color, es.other.color): es
      for es in initial.next_corner.keys()
    }
    existing_corners = {
      (cs.color, cs.other.color): cs
      for cs in initial.next_edge.keys()
    }
  else:
    existing_edges = {}
    existing_corners = {}

  edge_cubies: dict[tuple[Color, Color], EdgeSticker] = {}

  def make_edge(a: Color, b: Color) -> None:
    '''Create or reuse one edge cubie with two directed stickers.'''
    if (a, b) in existing_edges:
      s_ab: EdgeSticker = existing_edges[(a, b)]
      s_ba: EdgeSticker = existing_edges[(b, a)]
    else:
      s_ab = EdgeSticker(a)
      s_ba = EdgeSticker(b)
      s_ab._rewire(s_ba)
      s_ba._rewire(s_ab)
    edge_cubies[(a, b)] = s_ab
    edge_cubies[(b, a)] = s_ba

  make_edge(color[Side.FRONT], color[Side.TOP])
  make_edge(color[Side.FRONT], color[Side.RIGHT])
  make_edge(color[Side.FRONT], color[Side.BOTTOM])
  make_edge(color[Side.FRONT], color[Side.LEFT])
  make_edge(color[Side.BACK],  color[Side.TOP])
  make_edge(color[Side.BACK],  color[Side.RIGHT])
  make_edge(color[Side.BACK],  color[Side.BOTTOM])
  make_edge(color[Side.BACK],  color[Side.LEFT])
  make_edge(color[Side.TOP],   color[Side.RIGHT])
  make_edge(color[Side.TOP],   color[Side.LEFT])
  make_edge(color[Side.BOTTOM],color[Side.RIGHT])
  make_edge(color[Side.BOTTOM],color[Side.LEFT])

  next_edge: dict[CornerSticker, EdgeSticker] = {}
  next_corner: dict[EdgeSticker, CornerSticker] = {}

  def make_corner(a: Color, b: Color, c: Color) -> CornerSticker:
    '''Create or reuse one corner cubie and wire local adjacencies.'''
    if (a, b) in existing_corners:
      s: tuple[CornerSticker, CornerSticker, CornerSticker] = (
        existing_corners[(a, b)],
        existing_corners[(b, c)],
        existing_corners[(c, a)],
      )
    else:
      s = (
        CornerSticker(a),
        CornerSticker(b),
        CornerSticker(c),
      )
      s[0]._rewire(s[1])
      s[1]._rewire(s[2])
      s[2]._rewire(s[0])

    for i in range(3):
      curr: CornerSticker = s[i]
      nxt: CornerSticker  = s[(i + 1) % 3]
      prv: CornerSticker  = s[(i - 1) % 3]
      c0: Color = curr.color
      c1: Color = nxt.color
      c2: Color = prv.color
      next_edge[curr]                    = edge_cubies[(c0, c2)]
      next_corner[edge_cubies[(c0, c1)]] = curr
    return s[0]

  home: CornerSticker = make_corner(
    color[Side.FRONT], color[Side.LEFT],   color[Side.TOP])
  make_corner(color[Side.FRONT], color[Side.TOP],    color[Side.RIGHT])
  make_corner(color[Side.FRONT], color[Side.RIGHT],  color[Side.BOTTOM])
  make_corner(color[Side.FRONT], color[Side.BOTTOM], color[Side.LEFT])
  make_corner(color[Side.BACK],  color[Side.RIGHT],  color[Side.TOP])
  make_corner(color[Side.BACK],  color[Side.BOTTOM], color[Side.RIGHT])
  make_corner(color[Side.BACK],  color[Side.LEFT],   color[Side.BOTTOM])
  make_corner(color[Side.BACK],  color[Side.TOP],    color[Side.LEFT])

  return Cube(
    home=home,
    front_color=color[Side.FRONT],
    top_color=color[Side.TOP],
    next_edge=next_edge,
    next_corner=next_corner,
  )

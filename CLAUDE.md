@python.md

# rubik-cube-model

An orientation-independent model of the Rubik's Cube. The model can be used
to study properties of the cube, study and discover solution methods and
algorithms, and build cube games. All operations are defined using only
relative navigation — no absolute coordinates are ever computed or used.

## Model Overview

The cube is represented as 48 colored stickers, one for each non-center
position on all faces. Center stickers are not modeled as objects; the color
of each face's center is implicit in the `front_color` and `top_color` fields
of `Cube`.

### Sticker Types

Corner cubies use `CornerSticker` and edge cubies use `EdgeSticker`; both
subclass the abstract `Sticker`. Each sticker has a `color` (a `Color` enum
value) and an `other` pointer.

- On a corner cubie, the three `CornerSticker`s form a circular linked list
  via `other`, ordered clockwise as seen from outside the cube.
- On an edge cubie, the two `EdgeSticker`s form a 2-cycle via `other`.

### Face Adjacency Maps

`Cube` holds two dicts that encode clockwise sticker order on each face:

- `next_edge: dict[CornerSticker, EdgeSticker]` — from a corner sticker to
  the next edge sticker clockwise on the same face.
- `next_corner: dict[EdgeSticker, CornerSticker]` — from an edge sticker to
  the next corner sticker clockwise on the same face.

These two dicts are always inverses of each other: `next_corner[next_edge[c]]
is c` for every corner sticker `c`, and vice versa.

Traversing a full face ring by alternating `next_edge` and `next_corner`
visits 4 corner stickers and 4 edge stickers interleaved, in clockwise order.

### Orientation

`Cube` carries three orientation fields:

- `home: CornerSticker` — points to the sticker in the upper-left corner of
  the front face, on the front face itself (green in a solved cube with the
  default color assignment).
- `front_color: Color` — the color of the front face's center.
- `top_color: Color` — the color of the top face's center.

Together these three fields fully determine the cube's orientation. No other
orientation state exists. Calculations that depend on the cube's orientation
use `home` as their starting point.

Equality on stickers is determined by color and other.color.
It follows that standard dataclass equality makes cubes
equal exactly when they are in the same position and
the same orientation.

## Navigation

Navigation is the only way to move between stickers. There are two primitive
steps, encoded by the `Nav` enum:

- `Nav.NEXT` (`'N'`) — move to the next sticker clockwise on the same face,
  crossing the cubie boundary (corner → edge or edge → corner).
- `Nav.OTHER` (`'O'`) — move to the next sticker on the same cubie
  (corner → corner, or edge → edge).

`Nav.NEXT` always alternates the sticker type: a sequence with an even number
of `NEXT` steps ends on the same type it started on; a sequence with an odd
number ends on the opposite type.

`nav(nav_path, cube, sticker)` applies a sequence of `Nav` steps
starting from any sticker on the cube and returns a `Sticker`.

`nav_cc(nav_path, cube, sticker)` is a convenience function for the
common case of corner-to-corner navigation; it returns
`CornerSticker` directly, simplifying call sites that know the result must be
a corner.

`parse_navs(text)` converts a string of `'N'` and `'O'` characters into a
`list[Nav]`.

### Navigation to Sides

`corner_on_side(cube, side)` returns a representative `CornerSticker` on the
given side. `side_corners(cube, start)` returns all four corner stickers on
the same face as `start`, in clockwise order.

#### Implementation detail

`HOME_TO_SIDE: dict[Side, list[Nav]]` caches the navigation path from
`cube.home` to the representative corner sticker on each side. This dict also
implicitly defines which corner is the representative for each side, a
question that may warrant a cleaner interface in future.

| Side     | Path       |
|----------|------------|
| `FRONT`  | `''`       |
| `TOP`    | `'OO'`     |
| `RIGHT`  | `'NNOO'`   |
| `LEFT`   | `'O'`      |
| `BOTTOM` | `'ONNOO'`  |
| `BACK`   | `'OONNOO'` |

### Color/Side Lookup

`side_color(cube, side)` returns the center `Color` of the given side.
`color_side(cube, color)` returns the `Side` whose center has the given color.
`all_colors(cube)` returns the eight non-center sticker colors for each side
by traversing the face ring.

#### Implementation detail

`side_colors` and `color_sides` are module-level dicts precomputed at import
time from a solved cube. They map `(front_color, top_color, side)` to the
center color of that side, and `(front_color, top_color, center_color)` to the
corresponding `Side`, for every valid orientation. The table is keyed on
`(s.color, s.other.other.color, side)` during construction, where `s` is a
corner sticker: `s.color` is the front-face color and `s.other.other.color`
is the top-face color of that sticker's cubie, matching the `front_color` and
`top_color` fields of `Cube`.

## Face Moves

A `Move` is a `Side` and a `Multiplicity`. `Multiplicity` is `CW` for
clockwise, `CCW` for counterclockwise, or `TWO` for a double twist (which is
the same in either direction).

`move(m, cube)` applies the move in place. `moved(m, cube)` is
the immutable version: it returns a new cube with the move applied, leaving
the original unchanged.

A face move is strictly local: everything on the face being turned stays fixed
relative to that face. The only things that change are the `next_edge` and
`next_corner` links between the ring of stickers on the side of the turning
face and their neighbors on the stationary part of the cube.

The cube's orientation does not change during a move. However, `cube.home` is
a pointer to a specific sticker object, and that sticker physically moves
during a front, top, or left face turn, carrying the home pointer away from
the home position. After such a move the pointer must be updated to the
sticker now occupying the home position. Right, bottom, and back moves do not
displace the home sticker, so no update is needed for those.

#### Implementation detail

`_move_corner` identifies the ring stickers that participate in the rewiring:

- `corners_oo` — for each of the four face corners, the sticker reached by
  `.other.other`, i.e. the sticker on the same cubie that faces the adjacent
  stationary face.
- `edges_no` — for each `corners_oo` sticker, the edge sticker reached via
  `next_edge` then `.other`, i.e. the edge sticker facing the adjacent
  stationary face.

It then cycles `next_edge[corners_oo[i]]` and `next_corner[edges_no[i]]` in
the appropriate direction. No sticker object moves; only the links change.

`_move_home` updates `cube.home` after moves that displace it. `restore_home`
caches the navigation path from the displaced sticker back to the new home
position, keyed by `(Side, Multiplicity)`.

## Reachability

`reachable(cube)` returns `True` if and only if the cube position can be
reached from the solved state by a sequence of face moves. It checks three
independent criteria, each corresponding to a conserved quantity that every
face move preserves.

These three criteria together are also sufficient -
if all three criteria are satisfied, the cube position can be
reached from the solved state by a sequence of face moves.

A cube can be solved if and only if it can be reached from the
solved state: given a sequence of moves to reach the cube position
from the solved state, you can solve the cube by reversing the
sequence and reversing the direction of each move.

### Permutation parity (`locations_ok`)

Each face move cycles 4 corner cubies and 4 edge cubies simultaneously. A
4-cycle is an odd permutation, so every move changes the parity of both the
corner permutation and the edge permutation by the same amount. The two
parities therefore always stay equal. `locations_ok` verifies this by
computing the permutation that takes the current corner-cubie order to the
solved order, and likewise for edge cubies, and checking that both
permutations are even or both are odd.

Cubies are identified by the frozenset of their sticker colors. The ordering
is produced by `_all_corners` and `_all_edges`, which enumerate cubies in a
fixed sequence via navigation from `cube.home` and `corner_on_side(BACK)`.

### Edge flip parity (`edge_flips_ok`)

Each edge cubie has a well-defined orientation: it is either in its natural
state or flipped 180°. To measure this without absolute coordinates, each
edge cubie has a representative sticker (the one whose color ranks first in
the priority order blue > green > white > yellow) and a representative face
(the face among the two it straddles whose center color ranks first in the
same order). The cubie is flipped if its representative sticker is not on its
representative face.

Every face move flips an even number of edge cubies (in fact exactly 0 or 4
depending on the axis of the turn), so the total flip count is always even.
`edge_flips_ok` counts the flipped cubies and checks that the count is even.

### Corner rotation sum (`corner_rotations_ok`)

Each corner cubie has a rotation number 0, 1, or 2, measured in units of
120° clockwise as seen from outside the cube. The rotation is determined by
which face the white-or-yellow sticker of the cubie lands on: 0 if it is on a
white/yellow face, 1 if rotating the cubie 120° clockwise would put it there
(i.e. `r.other` is on a white/yellow face), and 2 otherwise.

Every face move changes the rotation sum by a multiple of 3, so the sum is
always divisible by 3. `corner_rotations_ok` sums the rotation numbers of all
8 corners and checks divisibility.

#### Implementation detail

`_all_corners` and `_all_edges` are generators. `_all_corners` yields from
`side_corners(cube.home)` then `side_corners(corner_on_side(BACK))`, covering
all 8 corner cubies. `_all_edges` yields `next_edge[c]` for each front corner
(4 front-ring edges), `next_edge[c.other.other]` for each front corner (4
middle-layer edges), and `next_edge[c]` for each back corner (4 back-ring
edges), covering all 12 edge cubies.

## Creating Cubes

Two functions are provided for creating a new cube with all
navigation links pre-wired. One creates a cube in the solved state,
and the other creates a cube in a solvable randomly shuffled state.
If an initial cube is provided to either function, the sticker
objects of the initial cube are re-used; otherwise, a full set of
new sticker objects is created from scratch.

All functions that change the state of the cube are provided in two
versions: one version that modifies the cube in place, and an
immutable version that creates a new cube in the modified state
without modifying the supplied cube. In either case, the sticker
objects of the supplied cube are re-used, and no new sticker objects
are created.

## Conventions Specific to This Project

- Never use absolute coordinates, indices, or position arithmetic. All
  traversal must use `nav`, `next_edge`, `next_corner`, and/or `.other`.
- There are three equivalent ways to express a navigation path, each with
  different tradeoffs:
  - `'NO...'` strings via `parse_navs` — most concise and readable, least
    efficient.
  - `list[Nav]` literals — intermediate in both clarity and efficiency.
  - Direct use of `.other`, `next_edge`, and `next_corner` — most efficient,
    most verbose.
  Use whichever form best fits the context.
- All source modules use `from __future__ import annotations` to satisfy mypy
  under Python 3.14 without requiring quoted forward references. This is
  intentional; do not remove it until mypy supports deferred annotation
  evaluation on 3.14+ without it.
- When modifying any code described in an Implementation detail section
  of this file, update that section to match.

## Cube Rotations
- Use `rotate(Move, Cube)` and `rotated(Move, Cube)` for rigid rotations of the cube
- Use `act(Action, Cube)` and `acted(Action, Cube)` for applying actions

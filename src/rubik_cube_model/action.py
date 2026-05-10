'''Standard Rubik's cube move notation: actions, parsing, and dispatch.

Action is the union Move | Rotation | WideMove | SliceMove.
Rotation, WideMove, and SliceMove are frozen dataclasses wrapping a
Move, distinct concrete types at runtime while serving as newtypes of
Move at the type-checker level.

act(action, cube) applies an action in place.
acted(action, cube) returns a new cube with the action applied.

Decompositions:
  WideMove(m)  — rotate(m, cube); move(Move(opp_side[m.face], m.mult), cube)
  SliceMove(m) — rotate(m, cube); move(Move(opp_side[m.face], m.mult), cube);
                 move(Move(m.face, invert[m.mult]), cube)

parse_actions(s, ci=False) parses standard Rubik's cube move notation.
Tokens may be written with or without spaces between them. Each token
is a base letter followed by an optional modifier: nothing (CW),
apostrophe (CCW), or 2 (TWO).

Standard notation:
  Face moves:  U D F B L R
  Rotations:   x y z
  Wide moves:  u d f b l r  or  Uw Dw Fw Bw Lw Rw
  Slice moves: M E S

When ci=True, all letters are folded to uppercase. Bare lowercase
letters parse as face moves. Wide moves require the w or W suffix.
'''

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .model import Cube, Side, opp_side, shallow_copy
from .move import Move, Multiplicity, invert, move
from .rotate import rotate


@dataclass(frozen=True)
class Rotation:
    '''A rigid cube rotation (x, y, z); newtype of Move.'''
    move: Move


@dataclass(frozen=True)
class WideMove:
    '''A wide two-layer move; newtype of Move.'''
    move: Move


@dataclass(frozen=True)
class SliceMove:
    '''A middle-layer slice move (M, E, S); newtype of Move.'''
    move: Move


# Any action representable in standard Rubik's cube notation.
type Action = Move | Rotation | WideMove | SliceMove

# An iterator of Action values.
type Actions = Iterator[Action]

_MULT_SUFFIX: dict[str, Multiplicity] = {
    '':  Multiplicity.CW,
    "'": Multiplicity.CCW,
    '2': Multiplicity.TWO,
}

_FACE_SIDE: dict[str, Side] = {
    'U': Side.TOP,
    'D': Side.BOTTOM,
    'F': Side.FRONT,
    'B': Side.BACK,
    'L': Side.LEFT,
    'R': Side.RIGHT,
}

_ROTATION_SIDE: dict[str, Side] = {
    'x': Side.RIGHT,
    'y': Side.TOP,
    'z': Side.FRONT,
}

_WIDE_SIDE: dict[str, Side] = {
    'u': Side.TOP,
    'd': Side.BOTTOM,
    'f': Side.FRONT,
    'b': Side.BACK,
    'l': Side.LEFT,
    'r': Side.RIGHT,
}

_SLICE_SIDE: dict[str, Side] = {
    'M': Side.LEFT,
    'E': Side.BOTTOM,
    'S': Side.FRONT,
}


class ParseError(ValueError):
    '''Raised when a move token cannot be parsed.'''


def _parse_mult(s: str, pos: int) -> tuple[Multiplicity, int]:
    '''Parse a multiplicity modifier at pos, returning (mult, new_pos).'''
    if pos < len(s) and s[pos] == "'":
        return Multiplicity.CCW, pos + 1
    if pos < len(s) and s[pos] == '2':
        return Multiplicity.TWO, pos + 1
    return Multiplicity.CW, pos


def _parse_one(s: str, pos: int, ci: bool) -> tuple[Action, int]:
    '''Parse one token from s starting at pos.

    Returns (action, new_pos). Raises ParseError on invalid input.
    '''
    if pos >= len(s):
        raise ParseError(f'unexpected end of input at position {pos}')
    base: str = s[pos]
    pos += 1

    # w/W suffix: wide move. Valid for any face letter, either case.
    if pos < len(s) and s[pos] in ('w', 'W'):
        pos += 1
        mult, pos = _parse_mult(s, pos)
        upper: str = base.upper()
        if upper not in _FACE_SIDE:
            raise ParseError(
                f'unknown wide-move face {base!r}'
            )
        return WideMove(Move(_FACE_SIDE[upper], mult)), pos

    if ci:
        upper = base.upper()
        mult, pos = _parse_mult(s, pos)
        if upper in _FACE_SIDE:
            return Move(_FACE_SIDE[upper], mult), pos
        if upper in ('X', 'Y', 'Z'):
            return Rotation(Move(_ROTATION_SIDE[base.lower()], mult)), pos
        if upper in ('M', 'E', 'S'):
            return SliceMove(Move(_SLICE_SIDE[upper], mult)), pos
        raise ParseError(f'unknown move letter {base!r}')

    mult, pos = _parse_mult(s, pos)
    if base in _FACE_SIDE:
        return Move(_FACE_SIDE[base], mult), pos
    if base in _ROTATION_SIDE:
        return Rotation(Move(_ROTATION_SIDE[base], mult)), pos
    if base in _WIDE_SIDE:
        return WideMove(Move(_WIDE_SIDE[base], mult)), pos
    if base in _SLICE_SIDE:
        return SliceMove(Move(_SLICE_SIDE[base], mult)), pos
    raise ParseError(f'unknown move letter {base!r}')


def parse_actions(s: str, ci: bool = False) -> list[Action]:
    '''Parse standard Rubik's cube move notation into a list of actions.

    Tokens may be separated by optional whitespace. Each token is a
    base letter followed by an optional modifier: nothing (CW),
    apostrophe (CCW), or 2 (TWO).

    Raises ParseError on unrecognised letters or modifiers.
    '''
    actions: list[Action] = []
    pos: int = 0
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue
        action, pos = _parse_one(s, pos, ci)
        actions.append(action)
    return actions


def act(action: Action, cube: Cube) -> None:
    '''Apply an action to a cube in place.'''
    match action:
        case Rotation(move=m):
            rotate(m, cube)
        case WideMove(move=m):
            rotate(m, cube)
            move(Move(opp_side[m.face], m.mult), cube)
        case SliceMove(move=m):
            rotate(m, cube)
            move(Move(opp_side[m.face], m.mult), cube)
            move(Move(m.face, invert[m.mult]), cube)
        case Move() as m:
            move(m, cube)


def acted(action: Action, cube: Cube) -> Cube:
    '''Return a new cube with an action applied, leaving the original unchanged.'''
    new: Cube = shallow_copy(cube)
    act(action, new)
    return new

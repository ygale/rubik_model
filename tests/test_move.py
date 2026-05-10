'''Tests for cube moves.'''

import pytest
from cube_integrity import check_cube_integrity
from rubik_cube_model import (
    Move,
    Multiplicity,
    Side,
    moved,
    solved,
)

_ALL_MOVES: list[Move] = [
    Move(side, mult)
    for side in Side
    for mult in Multiplicity
]

@pytest.mark.parametrize('m', _ALL_MOVES, ids=str)
def test_integrity_after_move(m: Move) -> None:
    '''Integrity holds after applying each single move to a solved cube.'''
    check_cube_integrity(moved(m, solved()))

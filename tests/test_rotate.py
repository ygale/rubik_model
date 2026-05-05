'''Tests for rigid cube rotations.'''

from rubik_cube_model import (
    Color,
    Move,
    Multiplicity,
    Side,
    all_colors,
    solved,
    rotate,
    rotated,
)

def test_rotate_front_cw() -> None:
    '''Test rigid CW rotation around the FRONT face.'''
    cube = solved()
    rotate(Move(Side.FRONT, Multiplicity.CW), cube)
    colors = all_colors(cube)

    assert all(c == Color.GREEN  for c in colors[Side.FRONT])
    assert all(c == Color.WHITE  for c in colors[Side.RIGHT])
    assert all(c == Color.ORANGE for c in colors[Side.TOP])
    assert all(c == Color.RED    for c in colors[Side.BOTTOM])
    assert all(c == Color.YELLOW for c in colors[Side.LEFT])
    assert all(c == Color.BLUE   for c in colors[Side.BACK])

def test_rotated_immutability() -> None:
    '''Test that rotated does not mutate the original cube.'''
    cube = solved()
    new_cube = rotated(Move(Side.RIGHT, Multiplicity.CCW), cube)

    colors = all_colors(cube)
    assert all(c == Color.GREEN for c in colors[Side.FRONT])
    assert all(c == Color.WHITE for c in colors[Side.TOP])

    new_colors = all_colors(new_cube)
    assert all(c == Color.WHITE for c in new_colors[Side.FRONT])

def test_rotate_four_times() -> None:
    '''Test that rotating four times CW returns to solved state.'''
    cube = solved()
    move = Move(Side.TOP, Multiplicity.CW)
    for _ in range(4):
        rotate(move, cube)

    assert cube == solved(initial=cube)

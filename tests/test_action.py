'''Tests for action.py: move notation parsing and dispatch.'''

from __future__ import annotations

import pytest
from rubik_cube_model.action import (
    Action,
    ParseError,
    Rotation,
    SliceMove,
    WideMove,
    act,
    acted,
    parse_actions,
)
from rubik_cube_model.model import Side, opp_side
from rubik_cube_model.move import Move, Multiplicity, invert, move
from rubik_cube_model.rotate import rotate
from rubik_cube_model import Color, all_colors, solved
from cube_integrity import check_cube_integrity


def _face(side: Side, mult: Multiplicity) -> Move:
    '''Convenience constructor for a plain face Move.'''
    return Move(side, mult)


def _rot(side: Side, mult: Multiplicity) -> Rotation:
    '''Convenience constructor for a Rotation.'''
    return Rotation(Move(side, mult))


def _wide(side: Side, mult: Multiplicity) -> WideMove:
    '''Convenience constructor for a WideMove.'''
    return WideMove(Move(side, mult))


def _slice(side: Side, mult: Multiplicity) -> SliceMove:
    '''Convenience constructor for a SliceMove.'''
    return SliceMove(Move(side, mult))


class TestFaceMoves:
    '''Tests for standard face-move tokens.'''

    def test_U_cw(self) -> None:
        '''U parses as TOP CW.'''
        assert parse_actions('U') == [_face(Side.TOP, Multiplicity.CW)]

    def test_D_ccw(self) -> None:
        '''D apostrophe parses as BOTTOM CCW.'''
        assert parse_actions("D'") == [_face(Side.BOTTOM, Multiplicity.CCW)]

    def test_F2(self) -> None:
        '''F2 parses as FRONT TWO.'''
        assert parse_actions('F2') == [_face(Side.FRONT, Multiplicity.TWO)]

    def test_B_cw(self) -> None:
        '''B parses as BACK CW.'''
        assert parse_actions('B') == [_face(Side.BACK, Multiplicity.CW)]

    def test_L_ccw(self) -> None:
        '''L apostrophe parses as LEFT CCW.'''
        assert parse_actions("L'") == [_face(Side.LEFT, Multiplicity.CCW)]

    def test_R2(self) -> None:
        '''R2 parses as RIGHT TWO.'''
        assert parse_actions('R2') == [_face(Side.RIGHT, Multiplicity.TWO)]

    def test_spaced_sequence(self) -> None:
        '''Tokens separated by spaces parse correctly.'''
        assert parse_actions("R U R' U'") == [
            _face(Side.RIGHT, Multiplicity.CW),
            _face(Side.TOP, Multiplicity.CW),
            _face(Side.RIGHT, Multiplicity.CCW),
            _face(Side.TOP, Multiplicity.CCW),
        ]

    def test_spaceless_sequence(self) -> None:
        '''Tokens without spaces parse identically to spaced tokens.'''
        assert parse_actions("RUR'U'") == parse_actions("R U R' U'")


class TestRotations:
    '''Tests for cube rotation tokens.'''

    def test_x_cw(self) -> None:
        '''x parses as Rotation on RIGHT CW.'''
        assert parse_actions('x') == [_rot(Side.RIGHT, Multiplicity.CW)]

    def test_y_ccw(self) -> None:
        '''y apostrophe parses as Rotation on TOP CCW.'''
        assert parse_actions("y'") == [_rot(Side.TOP, Multiplicity.CCW)]

    def test_z2(self) -> None:
        '''z2 parses as Rotation on FRONT TWO.'''
        assert parse_actions('z2') == [_rot(Side.FRONT, Multiplicity.TWO)]

    def test_rotation_is_rotation_type(self) -> None:
        '''Parsed rotation has type Rotation.'''
        assert isinstance(parse_actions('x')[0], Rotation)


class TestWideMoves:
    '''Tests for wide-move tokens.'''

    def test_lowercase_u(self) -> None:
        '''u parses as WideMove on TOP CW.'''
        assert parse_actions('u') == [_wide(Side.TOP, Multiplicity.CW)]

    def test_lowercase_d_ccw(self) -> None:
        '''d apostrophe parses as WideMove on BOTTOM CCW.'''
        assert parse_actions("d'") == [_wide(Side.BOTTOM, Multiplicity.CCW)]

    def test_lowercase_f2(self) -> None:
        '''f2 parses as WideMove on FRONT TWO.'''
        assert parse_actions('f2') == [_wide(Side.FRONT, Multiplicity.TWO)]

    def test_w_suffix_upper(self) -> None:
        '''Uw parses as WideMove on TOP CW.'''
        assert parse_actions('Uw') == [_wide(Side.TOP, Multiplicity.CW)]

    def test_w_suffix_ccw(self) -> None:
        '''Rw apostrophe parses as WideMove on RIGHT CCW.'''
        assert parse_actions("Rw'") == [_wide(Side.RIGHT, Multiplicity.CCW)]

    def test_w_suffix_two(self) -> None:
        '''Lw2 parses as WideMove on LEFT TWO.'''
        assert parse_actions('Lw2') == [_wide(Side.LEFT, Multiplicity.TWO)]

    def test_wide_is_wide_type(self) -> None:
        '''Parsed wide move has type WideMove.'''
        assert isinstance(parse_actions('u')[0], WideMove)

    def test_spaceless_wide(self) -> None:
        '''Wide moves parse correctly without spaces.'''
        assert parse_actions("UwRw'") == [
            _wide(Side.TOP, Multiplicity.CW),
            _wide(Side.RIGHT, Multiplicity.CCW),
        ]


class TestSliceMoves:
    '''Tests for slice-move tokens.'''

    def test_M_cw(self) -> None:
        '''M parses as SliceMove on LEFT CW.'''
        assert parse_actions('M') == [_slice(Side.LEFT, Multiplicity.CW)]

    def test_E_ccw(self) -> None:
        '''E apostrophe parses as SliceMove on BOTTOM CCW.'''
        assert parse_actions("E'") == [_slice(Side.BOTTOM, Multiplicity.CCW)]

    def test_S2(self) -> None:
        '''S2 parses as SliceMove on FRONT TWO.'''
        assert parse_actions('S2') == [_slice(Side.FRONT, Multiplicity.TWO)]

    def test_slice_is_slice_type(self) -> None:
        '''Parsed slice move has type SliceMove.'''
        assert isinstance(parse_actions('M')[0], SliceMove)


class TestCaseInsensitiveDialect:
    '''Tests for ci=True parsing dialect.'''

    def test_uppercase_face_ci(self) -> None:
        '''Uppercase face letters parse as face moves in ci mode.'''
        assert parse_actions('U', ci=True) == [
            _face(Side.TOP, Multiplicity.CW)
        ]

    def test_lowercase_face_ci(self) -> None:
        '''Lowercase face letters parse as face moves in ci mode.'''
        assert parse_actions('u', ci=True) == [
            _face(Side.TOP, Multiplicity.CW)
        ]
        assert parse_actions("r'", ci=True) == [
            _face(Side.RIGHT, Multiplicity.CCW)
        ]

    def test_rotation_uppercase_ci(self) -> None:
        '''Uppercase X Y Z parse as rotations in ci mode.'''
        assert parse_actions('X', ci=True) == [
            _rot(Side.RIGHT, Multiplicity.CW)
        ]
        assert parse_actions('Y', ci=True) == [
            _rot(Side.TOP, Multiplicity.CW)
        ]
        assert parse_actions('Z', ci=True) == [
            _rot(Side.FRONT, Multiplicity.CW)
        ]

    def test_rotation_lowercase_ci(self) -> None:
        '''Lowercase x y z parse as rotations in ci mode.'''
        assert parse_actions('x', ci=True) == [
            _rot(Side.RIGHT, Multiplicity.CW)
        ]

    def test_wide_w_suffix_ci(self) -> None:
        '''w suffix parses wide moves in ci mode.'''
        assert parse_actions('Uw', ci=True) == [
            _wide(Side.TOP, Multiplicity.CW)
        ]
        assert parse_actions("Rw'", ci=True) == [
            _wide(Side.RIGHT, Multiplicity.CCW)
        ]

    def test_wide_W_suffix_ci(self) -> None:
        '''Capital W suffix also parses wide moves in ci mode.'''
        assert parse_actions('UW', ci=True) == [
            _wide(Side.TOP, Multiplicity.CW)
        ]
        assert parse_actions("rW'", ci=True) == [
            _wide(Side.RIGHT, Multiplicity.CCW)
        ]

    def test_slice_ci(self) -> None:
        '''Slice letters parse in either case in ci mode.'''
        assert parse_actions('M', ci=True) == [
            _slice(Side.LEFT, Multiplicity.CW)
        ]
        assert parse_actions('e', ci=True) == [
            _slice(Side.BOTTOM, Multiplicity.CW)
        ]

    def test_sequence_ci(self) -> None:
        '''Mixed sequence parses correctly in ci mode.'''
        assert parse_actions("RUwx2M'", ci=True) == [
            _face(Side.RIGHT, Multiplicity.CW),
            _wide(Side.TOP, Multiplicity.CW),
            _rot(Side.RIGHT, Multiplicity.TWO),
            _slice(Side.LEFT, Multiplicity.CCW),
        ]


class TestParseErrors:
    '''Tests for ParseError on invalid input.'''

    def test_invalid_letter(self) -> None:
        '''Unrecognised base letter raises ParseError.'''
        with pytest.raises(ParseError):
            parse_actions('Q')

    def test_invalid_modifier(self) -> None:
        '''Unrecognised modifier raises ParseError.'''
        with pytest.raises(ParseError):
            parse_actions('U3')

    def test_empty_string(self) -> None:
        '''Empty string produces an empty list.'''
        assert parse_actions('') == []

    def test_whitespace_only(self) -> None:
        '''Whitespace-only string produces an empty list.'''
        assert parse_actions('   \t\n') == []

    def test_bad_wide_suffix_letter(self) -> None:
        '''w suffix on unknown letter raises ParseError.'''
        with pytest.raises(ParseError):
            parse_actions('Qw')


class TestAct:
    '''Tests for act(): in-place action dispatch.'''

    def test_act_face_move(self) -> None:
        '''act() with a Move applies a face move and preserves integrity.'''
        cube = solved()
        act(Move(Side.RIGHT, Multiplicity.CW), cube)
        check_cube_integrity(cube)

    def test_act_face_move_changes_cube(self) -> None:
        '''act() with a Move changes the cube state.'''
        cube = solved()
        act(Move(Side.FRONT, Multiplicity.CW), cube)
        assert cube != solved()

    def test_act_rotation_changes_orientation(self) -> None:
        '''act() with a Rotation (z-CW) keeps GREEN on FRONT, WHITE on RIGHT.'''
        cube = solved()
        act(Rotation(Move(Side.FRONT, Multiplicity.CW)), cube)
        check_cube_integrity(cube)
        colors: dict[Side, list[Color]] = all_colors(cube)
        assert all(c == Color.GREEN for c in colors[Side.FRONT])
        assert all(c == Color.WHITE for c in colors[Side.RIGHT])

    def test_act_rotation_in_place(self) -> None:
        '''act() with a Rotation modifies the cube in place.'''
        cube = solved()
        act(Rotation(Move(Side.RIGHT, Multiplicity.CW)), cube)
        assert cube != solved()

    def test_act_wide_matches_decomposition(self) -> None:
        '''act() with WideMove matches manual rotate+move decomposition.'''
        m: Move = Move(Side.TOP, Multiplicity.CW)
        c1 = solved()
        act(WideMove(m), c1)
        c2 = solved()
        rotate(m, c2)
        move(Move(opp_side[m.face], m.mult), c2)
        assert c1 == c2

    def test_act_wide_changes_cube(self) -> None:
        '''act() with WideMove changes the cube state.'''
        cube = solved()
        act(WideMove(Move(Side.TOP, Multiplicity.CW)), cube)
        check_cube_integrity(cube)
        assert cube != solved()

    def test_act_wide_all_faces(self) -> None:
        '''WideMove CW applied 4 times returns to solved for every face.'''
        for face in Side:
            cube = solved()
            w: Action = WideMove(Move(face, Multiplicity.CW))
            for _ in range(4):
                act(w, cube)
            assert cube == solved(), f'WideMove {face.name} CW period != 4'

    def test_act_slice_matches_decomposition(self) -> None:
        '''act() with SliceMove matches manual decomposition.'''
        m: Move = Move(Side.LEFT, Multiplicity.CW)
        c1 = solved()
        act(SliceMove(m), c1)
        c2 = solved()
        rotate(m, c2)
        move(Move(opp_side[m.face], m.mult), c2)
        move(Move(m.face, invert[m.mult]), c2)
        assert c1 == c2

    def test_act_slice_changes_cube(self) -> None:
        '''act() with SliceMove changes the cube state.'''
        cube = solved()
        act(SliceMove(Move(Side.LEFT, Multiplicity.CW)), cube)
        check_cube_integrity(cube)
        assert cube != solved()

    def test_act_slice_all_faces(self) -> None:
        '''SliceMove CW returns to solved within 12 applications for every face.'''
        for face in Side:
            cube = solved()
            s: Action = SliceMove(Move(face, Multiplicity.CW))
            for n in range(1, 13):
                act(s, cube)
                if cube == solved():
                    break
            assert cube == solved(), (
                f'SliceMove {face.name} CW did not return to solved in 12'
            )

    def test_act_parsed_wide(self) -> None:
        '''act() dispatches correctly on a wide move from parse_actions.'''
        cube = solved()
        act(parse_actions('u')[0], cube)
        assert cube != solved()

    def test_act_parsed_slice(self) -> None:
        '''act() dispatches correctly on a slice move from parse_actions.'''
        cube = solved()
        act(parse_actions('M')[0], cube)
        assert cube != solved()

    def test_act_spaceless_sequence(self) -> None:
        '''act() over a spaceless-parsed face sequence preserves integrity.'''
        cube = solved()
        for action in parse_actions("RUR'U'"):
            act(action, cube)
        check_cube_integrity(cube)


class TestActed:
    '''Tests for acted(): immutable action dispatch.'''

    def test_acted_face_move(self) -> None:
        '''acted() returns a changed cube and preserves integrity.'''
        cube = solved()
        new_cube = acted(Move(Side.LEFT, Multiplicity.CCW), cube)
        check_cube_integrity(new_cube)
        assert new_cube != solved()

    def test_acted_face_move_immutable(self) -> None:
        '''acted() does not mutate the original cube.'''
        cube = solved()
        acted(Move(Side.TOP, Multiplicity.CW), cube)
        assert cube == solved()

    def test_acted_rotation(self) -> None:
        '''acted() with Rotation (y-CW) brings RED to FRONT.'''
        cube = solved()
        new_cube = acted(Rotation(Move(Side.TOP, Multiplicity.CW)), cube)
        check_cube_integrity(new_cube)
        colors: dict[Side, list[Color]] = all_colors(new_cube)
        assert all(c == Color.RED for c in colors[Side.FRONT])

    def test_acted_rotation_immutable(self) -> None:
        '''acted() with Rotation does not mutate the original.'''
        cube = solved()
        acted(Rotation(Move(Side.RIGHT, Multiplicity.CW)), cube)
        assert cube == solved()

    def test_acted_wide(self) -> None:
        '''acted() with WideMove returns correct cube.'''
        m: Move = Move(Side.FRONT, Multiplicity.CCW)
        c2 = solved()
        c1 = acted(WideMove(m), c2)
        check_cube_integrity(c1)
        rotate(m, c2)
        move(Move(opp_side[m.face], m.mult), c2)
        assert c1 == c2

    def test_acted_wide_immutable(self) -> None:
        '''acted() with WideMove does not mutate the original.'''
        cube = solved()
        acted(WideMove(Move(Side.TOP, Multiplicity.CW)), cube)
        assert cube == solved()

    def test_acted_slice(self) -> None:
        '''acted() with SliceMove returns correct cube.'''
        m: Move = Move(Side.FRONT, Multiplicity.CW)
        c2 = solved()
        c1 = acted(SliceMove(m), c2)
        check_cube_integrity(c1)
        rotate(m, c2)
        move(Move(opp_side[m.face], m.mult), c2)
        move(Move(m.face, invert[m.mult]), c2)
        assert c1 == c2

    def test_acted_slice_immutable(self) -> None:
        '''acted() with SliceMove does not mutate the original.'''
        cube = solved()
        acted(SliceMove(Move(Side.LEFT, Multiplicity.CW)), cube)
        assert cube == solved()

    def test_acted_wide_period(self) -> None:
        '''acted() with WideMove applied 4 times returns to solved.'''
        cube = solved()
        w: Action = WideMove(Move(Side.RIGHT, Multiplicity.CW))
        for _ in range(4):
            cube = acted(w, cube)
        assert cube == solved()

    def test_acted_sequence(self) -> None:
        '''acted() chained over a parsed face sequence preserves
        integrity.'''
        cube = solved()
        for action in parse_actions("R U R' U'"):
            cube = acted(action, cube)
        check_cube_integrity(cube)

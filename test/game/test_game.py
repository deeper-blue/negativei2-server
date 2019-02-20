"""Test cases for the Game class."""

import chess
import unittest
from server.game import Game, WHITE, BLACK

import fileinput
from os import listdir
from os.path import isfile, join, dirname, basename, splitext

import re
import copy

class GameTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Loads games from 'pgn' subdirectory into a dict.

        Usage:
            GameTest.moves['fools_mate'] # From pgn/fools_mate.pgn file
            #=> ['f3', 'e5', 'g4', 'Qh4']
        """
        cls.moves = dict()

        path = join(dirname(__file__), 'pgn')
        files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]

        flatten = lambda l: [item for sublist in l for item in sublist]

        for f in files:
            unflattened_moves = [re.sub(r'^\d+\. ', '', line.rstrip()).split() for line in fileinput.input(f)]
            cls.moves[basename(splitext(f)[0])] = flatten(unflattened_moves)

        return cls.moves

    def setUp(self):
        # Game with no players or time controls
        self.game = Game(1)

        # Game with time controls
        self.game_wt = Game(1, time_controls=60)

        # Finished game (zero time)
        self.game_ft = Game(1, time_controls=0)

        # Game with players (and no time controls)
        self.game_wp = Game(1)
        self.game_wp.add_player('1', side='w')
        self.game_wp.add_player('2', side='b')

        # Game with players and time controls
        self.game_wpt = Game(1, time_controls=60)
        self.game_wpt.add_player('1', side='w')
        self.game_wpt.add_player('2', side='b')

        # (Fool's Mate) (2 move checkmate for black) (Checkmate)
        self.test_game_1 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['fools_mate']:
            self.test_game_1.move(san)

        # (Yates–Znosko-Borovsky) (First capture on move 40) (Resignation)
        self.test_game_2 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['yates_znosko_borovsky']:
            self.test_game_2.move(san)

        # (Andreikin-Karjakin) (Short checkmate) (Checkmate)
        self.test_game_3 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['andreikin_karjakin']:
            self.test_game_3.move(san)

        # En passant with promotions
        self.test_game_4 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['ep_promotions']:
            self.test_game_4.move(san)

        # (Scholar's Mate) (4 move checkmate for white) (Checkmate)
        self.test_game_5 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['scholars_mate']:
            self.test_game_5.move(san)

        # Quickest stalemate
        self.test_game_6 = copy.deepcopy(self.game_wpt)
        for san in GameTest.moves['quickest_stalemate']:
            self.test_game_6.move(san)

    # NOTE: __init__ tests
    def test_init_invalid_id(self):
        """Invalid ID type."""
        self.assertRaises(TypeError, lambda: Game('1'))

    def test_init_invalid_time_control_type(self):
        """Invalid time control type."""
        self.assertRaises(TypeError, lambda: Game(1, time_controls='60'))

    def test_init_invalid_time_control_value(self):
        """Invalid time control value (negative int)."""
        self.assertRaises(ValueError, lambda: Game(1, time_controls=-60))

    def test_init_zero_time_control_result(self):
        """Time controls set to 0 (Each side has no time)."""
        self.assertEqual(self.game_ft.result, '1/2-1/2')
        self.assertEqual(self.game_ft.in_progress, False)

    # NOTE: Property initial value tests
    def test_initial_property_id(self):
        self.assertEqual(self.game.id, 1)

    def test_initial_property_board(self):
        self.assertEqual(self.game.board, chess.Board())

    def test_initial_property_players(self):
        self.assertEqual(self.game.players, {WHITE: None, BLACK: None})

    def test_initial_property_time_controls_int(self):
        self.assertEqual(self.game_wt.time_controls, 60)
    def test_property_time_controls_none(self):
        self.assertEqual(self.game.time_controls, None)

    def test_initial_property_remaining_time_int(self):
        self.assertEqual(self.game_wt.remaining_time, {WHITE: 60, BLACK: 60})
    def test_initial_property_remaining_time_none(self):
        self.assertEqual(self.game.remaining_time, {WHITE: None, BLACK: None})

    def test_initial_property_ply_count(self):
        self.assertEqual(self.game.ply_count, 0)

    def test_initial_property_move_count(self):
        self.assertEqual(self.game.move_count, 1)

    def test_initial_property_fen(self):
        self.assertEqual(self.game.fen, chess.STARTING_FEN)

    def test_initial_property_pgn(self):
        self.assertEqual(self.game.pgn, str())

    def test_initial_property_history(self):
        self.assertEqual(self.game.history, list())

    def test_initial_property_turn(self):
        self.assertEqual(self.game.turn, WHITE)

    def test_initial_property_free_slots(self):
        self.assertEqual(self.game.free_slots, 2)

    def test_initial_property_result(self):
        self.assertEqual(self.game.result, '*')

    def test_initial_property_in_progress(self):
        self.assertEqual(self.game.in_progress, True)

    def test_initial_property_game_over(self):
        self.assertEqual(self.game.game_over, {'game_over': False, 'reason': None})

    # NOTE: 'ply_count' property
    def test_prop_ply_count_short(self):
        """Play through test game 1 and check ply count."""
        self.assertEqual(self.test_game_1.ply_count, 4)

    def test_prop_ply_count_long(self):
        """Play through test game 2 and check ply count."""
        self.assertEqual(self.test_game_2.ply_count, 105)

    # NOTE: 'move_count' property
    def test_prop_move_count_short(self):
        """Play through test game 1 and check move count."""
        self.assertEqual(self.test_game_1.move_count, 3)

    def test_prop_move_count_long(self):
        """Play through a test game 2 and check move count."""
        self.assertEqual(self.test_game_2.move_count, 53)

    # NOTE: 'pgn' property
    def test_prop_pgn_short(self):
        """Play through test game 1 and check PGN string."""
        self.assertEqual(self.test_game_1.pgn, '1. f3 e5 2. g4 Qh4#')

    def test_prop_pgn_long(self):
        """Play through test game 2 and check PGN string."""
        self.assertEqual(self.test_game_2.pgn, '1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 Na5 9. Bc2 c5 10. d4 Qc7 11. h3 O-O 12. Nbd2 Bd7 13. Nf1 Nc6 14. d5 Nd8 15. g4 Ne8 16. Ng3 g6 17. Kh2 Ng7 18. Rg1 f6 19. Be3 Nf7 20. Rg2 Kh8 21. Qd2 Qc8 22. Rh1 Rg8 23. Rhg1 a5 24. Kh1 b4 25. c4 a4 26. Bd3 Qa6 27. Qe2 Raf8 28. Nd2 Qc8 29. f3 Ne8 30. Ndf1 Kg7 31. Bc1 h6 32. Ne3 Kh7 33. Rh2 Nh8 34. h4 Rf7 35. Nd1 Bf8 36. Nf2 Bg7 37. f4 Bf8 38. Qf3 Qd8 39. Nh3 Qe7 40. g5 Bxh3 41. f5 hxg5 42. hxg5 Rgg7 43. Rxh3+ Kg8 44. fxg6 Rxg6 45. Nf5 Qd7 46. Rg2 fxg5 47. Rgh2 Bg7 48. Rxh8+ Bxh8 49. Qh5 Rff6 50. Qxh8+ Kf7 51. Rh7+ Ng7 52. Rxg7+ Rxg7 53. Qxg7+')

    # NOTE: 'history' property
    def test_prop_history_short(self):
        """Play through test game 1 and check move history."""
        self.assertEqual(self.test_game_1.history, [
            {
                'san': 'f3',
                'side': 'w',
                'ply_count': 1,
                'move_count': 1,
                'piece': 'p',
                'from': 'f2',
                'to': 'f3',
                'promotion': {'promotion': False, 'piece': None},
                'capture': {'capture': False, 'piece': None},
                'castle': {'castle': False, 'side': None},
                'en_passant': {'en_passant': False, 'square': None}
            },
            {
                'san': 'e5',
                'side': 'b',
                'ply_count': 2,
                'move_count': 1,
                'piece': 'p',
                'from': 'e7',
                'to': 'e5',
                'promotion': {'promotion': False, 'piece': None},
                'capture': {'capture': False, 'piece': None},
                'castle': {'castle': False, 'side': None},
                'en_passant': {'en_passant': False, 'square': None}
            },
            {
                'san': 'g4',
                'side': 'w',
                'ply_count': 3,
                'move_count': 2,
                'piece': 'p',
                'from': 'g2',
                'to': 'g4',
                'promotion': {'promotion': False, 'piece': None},
                'capture': {'capture': False, 'piece': None},
                'castle': {'castle': False, 'side': None},
                'en_passant': {'en_passant': False, 'square': None}
            },
            {
                'san': 'Qh4',
                'side': 'b',
                'ply_count': 4,
                'move_count': 2,
                'piece': 'q',
                'from': 'd8',
                'to': 'h4',
                'promotion': {'promotion': False, 'piece': None},
                'capture': {'capture': False, 'piece': None},
                'castle': {'castle': False, 'side': None},
                'en_passant': {'en_passant': False, 'square': None}
            }
        ])

    def test_prop_history_long(self):
        """Play through test game 2 and check move history."""
        # No way I'm checking the entire dict for this game.
        self.assertEqual(len(self.test_game_2.history), 105)

    def test_prop_history_side(self):
        """Play through test game 2 and check the 'side' fields."""
        flatten = lambda l: [item for sublist in l for item in sublist]
        sides = [move['side'] for move in self.test_game_2.history]
        expected = [WHITE if i%2==1 else BLACK for i in range(1,106)]
        self.assertEqual(sides, expected)

    def test_prop_history_ply_count(self):
        """Play through test game 2 and check the 'ply_count' fields."""
        ply_counts = [move['ply_count'] for move in self.test_game_2.history]
        self.assertEqual(ply_counts, list(range(1,106)))

    def test_prop_history_move_count(self):
        """Play through test game 2 and check the 'move_count' fields."""
        move_counts = [move['move_count'] for move in self.test_game_2.history]
        l = list(range(1,53))
        expected = [j for i in zip(l, l) for j in i] + [53]
        self.assertEqual(move_counts, expected)

    def test_prop_history_piece(self):
        """Play through test game 3 and check the 'piece' fields."""
        piece_fields = [move['piece'] for move in self.test_game_3.history]
        self.assertEqual(piece_fields, ['p', 'p', 'n', 'n', 'n', 'p', 'p', 'p', 'n', 'b', 'b', 'n', 'n', 'b', 'q', 'k', 'n', 'k', 'n'])

    def test_prop_history_from(self):
        """Play through test game 3 and check the 'from' fields."""
        from_fields = [move['from'] for move in self.test_game_3.history]
        self.assertEqual(from_fields, ['c2', 'e7', 'b1', 'b8', 'g1', 'g7', 'd2', 'e5', 'c3', 'f8', 'c1', 'g8', 'f3', 'g7', 'd1', 'e8', 'd5', 'g8', 'f6'])

    def test_prop_history_to(self):
        """Play through test game 3 and check the 'to' fields."""
        to_fields = [move['to'] for move in self.test_game_3.history]
        self.assertEqual(to_fields, ['c4', 'e5', 'c3', 'c6', 'f3', 'g6', 'd4', 'd4', 'd5', 'g7', 'g5', 'e7', 'd4', 'd4', 'd4', 'g8', 'f6', 'h8', 'g4'])

    def test_prop_history_promotion(self):
        """Play through test game 4 and check the 'promotion' fields."""
        promotion_moves = list(filter(lambda move: move['promotion']['promotion'], self.test_game_4.history))
        promotion_pieces = [move['promotion']['piece'] for move in promotion_moves]
        self.assertEqual(promotion_pieces, ['b', 'n', 'r', 'q'])

    def test_prop_history_capture(self):
        """Play through test game 2 and check the 'capture' fields."""
        capture_moves = list(filter(lambda move: move['capture']['capture'], self.test_game_2.history))
        capture_pieces = [move['capture']['piece'] for move in capture_moves]
        self.assertEqual(capture_pieces, ['n', 'p', 'p', 'b', 'p', 'p', 'p', 'n', 'r', 'b', 'n', 'r', 'r'])

    def test_prop_history_castle(self):
        """Play through test game 2 and check the 'castle' fields."""
        castle_moves = list(filter(lambda move: move['castle']['castle'], self.test_game_2.history))
        castle_sides = [move['castle']['side'] for move in castle_moves]
        self.assertEqual(castle_sides, ['k', 'k'])

    def test_prop_history_en_passant(self):
        """Play through test game 4 and check the 'en_passant' fields."""
        ep_moves = list(filter(lambda move: move['en_passant']['en_passant'], self.test_game_4.history))
        ep_squares = [move['en_passant']['square'] for move in ep_moves]
        self.assertEqual(ep_squares, ['b5', 'd5', 'f5', 'h5'])

    # NOTE: 'turn' property
    def test_prop_turn_white(self):
        """Call property when it's white's turn."""
        self.assertEqual(self.game_wpt.turn, WHITE)

    def test_prop_turn_black(self):
        """Call property when it's black's turn."""
        self.game_wpt.move('e4')
        self.assertEqual(self.game_wpt.turn, BLACK)

    # NOTE: 'free_slots' property
    def test_prop_free_slots_no_players(self):
        """Call property with no players added."""
        self.assertEqual(self.game.free_slots, 2)

    def test_prop_free_slots_white(self):
        """Call property with only a white player added."""
        self.game.add_player('1', side='w')
        self.assertEqual(self.game.free_slots, 1)

    def test_prop_free_slots_black(self):
        """Call property with only a black player added."""
        self.game.add_player('1', side='b')
        self.assertEqual(self.game.free_slots, 1)

    def test_prop_free_slots_both(self):
        """Call property with both players added."""
        self.assertEqual(self.game_wpt.free_slots, 0)

    # NOTE: 'result' property
    def test_prop_result_1_0_without_time(self):
        """Call property when game is a win for white (1-0) not due to time."""
        self.assertEqual(self.test_game_5.result, '1-0')

    def test_prop_result_0_1_without_time(self):
        """Call property when game is a win for black (0-1) not due to time."""
        self.assertEqual(self.test_game_1.result, '0-1')

    def test_prop_result_draw_without_time(self):
        """Call property when game is a draw (1/2-1/2) not due to time."""
        self.assertEqual(self.test_game_6.result, '1/2-1/2')

    def test_prop_result_1_0_time(self):
        """Call property when game is a win for white (1-0) due to time."""
        self.game_wpt.time_delta(-60, side='b')
        self.assertEqual(self.game_wpt.result, '1-0')

    def test_prop_result_0_1_time(self):
        """Call property when game is a win for black (0-1) due to time."""
        self.game_wpt.time_delta(-60, side='w')
        self.assertEqual(self.game_wpt.result, '0-1')

    def test_prop_result_draw_time(self):
        """Call property when game is a draw due to time.

        NOTE: As explained in server/game.py, this case (when both sides run out of time)
            shouldn't occur in an actual game, but is included as a backup.
        """
        self.assertEqual(self.game_ft.result, '1/2-1/2')

    # NOTE: 'in_progress' property
    def test_prop_in_progress_when_in_progress(self):
        """Call property when game is in progress."""
        self.assertEqual(self.game.in_progress, True)

    def test_prop_in_progress_when_game_over(self):
        """Call property when game is over (test game 1)."""
        self.assertEqual(self.test_game_1.in_progress, False)

    # TODO: 'game_over' property

    # NOTE: 'add_player' function tests
    def test_add_player_invalid_side(self):
        """Add player to invalid side."""
        self.assertRaises(ValueError, lambda: self.game.add_player('1', side='z'))

    def test_add_player_invalid_id(self):
        """Add player with invalid ID."""
        self.assertRaises(TypeError, lambda: self.game.add_player(1, side='w'))

    def test_add_player_same_id(self):
        """Add player with same ID as player on opposite side."""
        self.game.add_player('1', side='w')
        self.assertRaises(RuntimeError, lambda: self.game.add_player('1', side='b'))

    def test_add_player_occupied(self):
        """Add two players to the same side."""
        self.game.add_player('1', side='w')
        self.assertRaises(RuntimeError, lambda: self.game.add_player('2', side='w'))

    def test_add_player_free(self):
        """Add two players to a game (with free slots)."""
        self.game.add_player('1', side='w')
        self.game.add_player('2', side='b')
        self.assertEqual(self.game.players, {WHITE: '1', BLACK: '2'})

    # NOTE: 'move' function tests
    def test_move_in_finished_game(self):
        """Make a move in a finished game."""
        self.assertRaises(RuntimeError, lambda: self.test_game_1.move('e4'))

    def test_move_with_no_players(self):
        """Make a move in a game with no players."""
        self.assertRaises(RuntimeError, lambda: self.game.move('e4'))

    def test_move_with_no_white_player(self):
        """Make a white-side move in a game with no white player."""
        self.game.add_player('1', side='b')
        self.assertRaises(RuntimeError, lambda: self.game.move('e4'))

    def test_move_with_no_black_player(self):
        """Make a black-side move in a game with no black player."""
        self.game.add_player('1', side='w')
        self.game.move('e4')
        self.assertRaises(RuntimeError, lambda: self.game.move('e5'))

    def test_move_with_invalid_san(self):
        """Make a move (with invalid SAN in the current context)."""
        self.assertRaises(ValueError, lambda: self.game_wpt.move('e6'))

    def test_move_increments_ply_count(self):
        """Making a move increments the ply count."""
        self.assertEqual(self.game_wpt.ply_count, 0)
        self.game_wpt.move('e4')
        self.assertEqual(self.game_wpt.ply_count, 1)

    def test_move_adds_san_field(self):
        """SAN for the made move is added as the value to the 'san' field."""
        move = self.game_wpt.move('Nf3')
        self.assertEqual(move['san'], 'Nf3')

    def test_move_adds_to_history(self):
        """Making a move adds it to self._history."""
        self.assertEqual(len(self.game_wpt.history), 0)
        self.game_wpt.move('e4')
        self.assertEqual(len(self.game_wpt.history), 1)

    # NOTE: 'time_delta' function tests
    def test_time_delta_invalid_side(self):
        """Make a time delta to an invalid side."""
        self.assertRaises(ValueError, lambda: self.game_wpt.time_delta(0, side='z'))

    def test_time_delta_invalid_delta(self):
        """Make an invalid time delta."""
        self.assertRaises(TypeError, lambda: self.game_wpt.time_delta(0.0))

    def test_time_delta_no_time_controls(self):
        """Make a time delta on a game with no time controls."""
        self.game_wp.time_delta(-5)
        self.assertEqual(self.game_wp.remaining_time, {WHITE: None, BLACK: None})

    def test_time_delta_finished_game(self):
        """Make a time delta on a finished (due to non-time reasons) game."""
        self.test_game_1.time_delta(-5)
        self.assertEqual(self.test_game_1.remaining_time, {WHITE: 60, BLACK: 60})

    def test_time_delta_positive(self):
        """Make a positive time delta."""
        self.game_wpt.time_delta(10)
        self.assertEqual(self.game_wpt.remaining_time[WHITE], 70)

    def test_time_delta_negative(self):
        """Make a negative time delta."""
        self.game_wpt.time_delta(-10)
        self.assertEqual(self.game_wpt.remaining_time[WHITE], 50)

    def test_time_delta_zero_reset(self):
        """Make a negative time delta which would set the time below zero."""
        self.game_wpt.time_delta(-55) # White has 5 seconds left after this time delta
        self.game_wpt.time_delta(-100)
        self.assertEqual(self.game_wpt.remaining_time[WHITE], 0)

    # NOTE: '_construct_move_description' function tests
    #   Most of the functionality for this function is actually tested in the 'history' property.
    def test_construct_move_description_wrong_move(self):
        """Construct move description of a move which isn't on the top of the move stack."""
        self.game_wpt.move('e4')
        move = chess.Move.from_uci('a7c6')
        self.assertRaises(ValueError, lambda: self.game_wpt._construct_move_description(move))

    def test_construct_move_description_correct_move(self):
        """Construct move description of a move which is on the top of the move stack."""
        move = self.game_wpt.board.push_san('Nc3')

        # Check that the move stack manipulation done by the function is okay
        self.assertEqual(self.game_wpt.board.peek(), move)
        desc = self.game_wpt._construct_move_description(move)
        self.assertEqual(self.game_wpt.board.peek(), move)

        # Check that the move description is correct
        self.assertEqual(desc, {
            'side': 'w',
            'ply_count': 0,
            'move_count': 1,
            'piece': 'n',
            'from': 'b1',
            'to': 'c3',
            'promotion': {'promotion': False, 'piece': None},
            'capture': {'capture': False, 'piece': None},
            'castle': {'castle': False, 'side': None},
            'en_passant': {'en_passant': False, 'square': None}
        })

    # NOTE: '_invert' function tests
    def test_invert_invalid_color(self):
        """Color inversion on invalid color."""
        self.assertRaises(ValueError, lambda: self.game._invert('z'))

    def test_invert_white(self):
        """Color inversion for white."""
        self.assertEqual(self.game._invert(WHITE), BLACK)

    def test_invert_black(self):
        """Color inversion for black."""
        self.assertEqual(self.game._invert(BLACK), WHITE)

    # TODO: '__str__' function tests
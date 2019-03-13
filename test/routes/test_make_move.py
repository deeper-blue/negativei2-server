"""Test cases for the POST server route /makemove."""

import unittest
import pytest
from server.server import app
from unittest.mock import patch
from .mock_firebase import MockClient

OK          = 200
BAD_REQUEST = 400

class MakeMoveTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/makemove'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /makemove?param_1=1&param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return MakeMoveTest.client.post(MakeMoveTest.route, data=data)

    def setUp(self):
        self.params = {'game_id': None, 'user_id': None, 'move': None}
        self.mock_game = {
            'id': 'some_game',
            'creator': 'some_creator',
            'players': {'w': 'some_player_1', 'b': 'some_player_2'},
            'free_slots': 2,
            'time_controls': None,
            'remaining_time': {'w': None, 'b': None},
            'resigned': {'w': False, 'b': False},
            'draw_offers': {
                'w': {'made': False, 'accepted': False},
                'b': {'made': False, 'accepted': False}
            },
            'in_progress': True,
            'result': '*',
            'game_over': {'game_over': False, 'reason': None},
            'turn': 'w',
            'ply_count': 0,
            'move_count': 1,
            'pgn': '',
            'history': [],
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'initial_positions': {'a1': 'a1', 'a2': 'a2', 'a7': 'a7', 'a8': 'a8', 'b1': 'b1', 'b2': 'b2', 'b7': 'b7', 'b8': 'b8', 'c1': 'c1', 'c2': 'c2', 'c7': 'c7', 'c8': 'c8', 'd1': 'd1', 'd2': 'd2', 'd7': 'd7', 'd8': 'd8', 'e1': 'e1', 'e2': 'e2', 'e7': 'e7', 'e8': 'e8', 'f1': 'f1', 'f2': 'f2', 'f7': 'f7', 'f8': 'f8', 'g1': 'g1', 'g2': 'g2', 'g7': 'g7', 'g8': 'g8', 'h1': 'h1', 'h2': 'h2', 'h7': 'h7', 'h8': 'h8'}
        }

    def fill_params(self, game_id=None, user_id=None, move=None):
        self.params['game_id'] = game_id
        self.params['user_id'] = user_id
        self.params['move']    = move

    def set_up_mock_db(self, mock_db):
        """Creates some entries in the mock database"""
        mock_db.collection("users").add({}, document_id='some_creator')
        mock_db.collection("users").add({}, document_id='some_player_1')
        mock_db.collection("users").add({}, document_id='some_player_2')
        mock_db.collection("games").add(self.mock_game, document_id='some_game')

    # Tests

    @patch('server.server.db', new_callable=MockClient)
    def test_game_doesnt_exist(self, mock_db):
        """Make a move on a game that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='game_that_doesnt_exist', user_id='some_player_1', move='e4')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_game_exists(self, mock_db):
        """Make a move on a game that exists."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', move='e4')
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @pytest.mark.skip(reason = "Need to decide how open slots will be dealt with")
    @patch('server.server.db', new_callable=MockClient)
    def test_user_id_open_slot(self, mock_db):
        """Make a move with the user ID set as the open slot."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='OPEN', move='e4')
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @pytest.mark.skip(reason = "Need to decide how AI slots will be dealt with")
    @patch('server.server.db', new_callable=MockClient)
    def test_user_id_ai_slot(self):
        """Make a move with the user ID set as the AI slot."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='AI', move='e4')
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_id_doesnt_exist(self, mock_db):
        """Make a move with the ID of a user that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='user_that_doesnt_exist', move='e4')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_not_in_game(self, mock_db):
        """Make a move with the ID of a user that exists, but isn't a player in the game."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_creator', move='e4')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_wrong_turn(self, mock_db):
        """Make a move from the player whose side it isn't to play."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_2', move='e4')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_correct_turn(self, mock_db):
        """Make a move from the player whose side it is to play."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', move='e4')
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_game_over(self, mock_db):
        """Make a move in a game which is over."""
        self.mock_game['resigned']['w'] = True
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', move='e4')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_move_invalid_san_notation(self, mock_db):
        """Make a move with invalid SAN notation."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', move='wrong_notation')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_move_invalid_san_context(self, mock_db):
        """Make a move which is valid SAN, but invalid in the current context."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', move='Nc6')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

"""Test cases for the POST server route /makemove."""

import unittest
import pytest
import json
from server.server import app
from unittest.mock import patch
from .mock_firebase import MockClient

OK          = 200
BAD_REQUEST = 400

class DrawOfferTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/drawoffer'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /drawoffer?param_1=1&param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return DrawOfferTest.client.post(DrawOfferTest.route, data=data)

    def setUp(self):
        self.params = {'game_id': None, 'user_id': None}
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
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        }

    def fill_params(self, game_id=None, user_id=None):
        self.params['game_id'] = game_id
        self.params['user_id'] = user_id

    def set_up_mock_db(self, mock_db):
        """Creates some entries in the mock database"""
        mock_db.collection("users").add({}, document_id='some_creator')
        mock_db.collection("users").add({}, document_id='some_player_1')
        mock_db.collection("users").add({}, document_id='some_player_2')
        mock_db.collection("games").add(self.mock_game, document_id='some_game')

    # Tests

    @patch('server.server.db', new_callable=MockClient)
    def test_game_doesnt_exist(self, mock_db):
        """Offer a draw offer on a game that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='game_that_doesnt_exist', user_id='some_player_1')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_game_exists(self, mock_db):
        """Offer a draw on a game that exists."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1')
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_id_doesnt_exist(self, mock_db):
        """Offer a draw with the ID of a user that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='user_that_doesnt_exist')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_not_in_game(self, mock_db):
        """Offer a draw with the ID of a user that exists, but isn't a player in the game."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_creator')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_offer_made(self, mock_db):
        """Check that a draw offer is actually made."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1')
        response = json.loads(self.post(self.params).data)
        self.assertEqual(response['draw_offers']['w']['made'], True)
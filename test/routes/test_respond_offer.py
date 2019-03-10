"""Test cases for the POST server route /respondoffer."""

import unittest
import pytest
import json
from server.server import app
from unittest.mock import patch
from .mock_firebase import MockClient

OK          = 200
BAD_REQUEST = 400

class RespondOfferTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/respondoffer'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            Making a POST request to /respondoffer with params {param_1: 1, param_2: 2} can be done with:
            response = self.post({param_1: 1, param_2: 2})
        """
        return RespondOfferTest.client.post(RespondOfferTest.route, data=data)

    def setUp(self):
        self.params = {'game_id': None, 'user_id': None, 'response': None}
        self.mock_game = {
            'id': 'some_game',
            'creator': 'some_creator',
            'players': {'w': 'some_player_1', 'b': 'some_player_2'},
            'free_slots': 2,
            'time_controls': None,
            'remaining_time': {'w': None, 'b': None},
            'resigned': {'w': False, 'b': False},
            'draw_offers': {
                'w': {'made': True, 'accepted': False},
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

    def fill_params(self, game_id=None, user_id=None, response=None):
        self.params['game_id'] = game_id
        self.params['user_id'] = user_id
        self.params['response'] = response

    def set_up_mock_db(self, mock_db):
        """Creates some entries in the mock database"""
        mock_db.collection("users").add({}, document_id='some_creator')
        mock_db.collection("users").add({}, document_id='some_player_1')
        mock_db.collection("users").add({}, document_id='some_player_2')
        mock_db.collection("games").add(self.mock_game, document_id='some_game')

    # Tests

    @patch('server.server.db', new_callable=MockClient)
    def test_game_doesnt_exist(self, mock_db):
        """Respond to a draw offer on a game that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='game_that_doesnt_exist', user_id='some_player_1', response=True)
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_game_exists(self, mock_db):
        """Respond to a draw offer on a game that exists."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_1', response=True)
        response = self.post(self.params)
        self.assertEqual(OK, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_id_doesnt_exist(self, mock_db):
        """Respond to a draw offer with the ID of a user that doesn't exist."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='user_that_doesnt_exist', response=True)
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_user_not_in_game(self, mock_db):
        """Respond to a draw offer with the ID of a user that exists, but isn't a player in the game."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_creator', response=True)
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_offer_accepted(self, mock_db):
        """Check that a draw offer is actually accepted."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_2', response=True)
        response = json.loads(self.post(self.params).data)
        self.assertEqual(response['draw_offers']['w']['accepted'], True)

    @patch('server.server.db', new_callable=MockClient)
    def test_offer_declined(self, mock_db):
        """Check that a draw offer is actually declined (and the made field is reset)."""
        self.set_up_mock_db(mock_db)
        self.fill_params(game_id='some_game', user_id='some_player_2', response=False)
        response = json.loads(self.post(self.params).data)
        self.assertEqual(response['draw_offers']['w']['made'], False)
        self.assertEqual(response['draw_offers']['w']['accepted'], False)
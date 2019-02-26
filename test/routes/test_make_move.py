"""Test cases for the POST server route /makemove."""

import unittest
from server.server import app
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

    def fill_params(self, game_id=None, user_id=None, move=None):
        self.params['game_id'] = game_id
        self.params['user_id'] = user_id
        self.params['move']    = move

    # Tests

    def test_invalid_game_id(self):
        self.fill_params(game_id='game_that_doesnt_exist')
        response = self.post(self.params)
        self.assertEqual(BAD_REQUEST, response.status_code)
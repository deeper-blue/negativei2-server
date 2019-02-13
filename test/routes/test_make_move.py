"""Test cases for the POST server route /makemove."""

import unittest
from server.server import app

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

    # Tests

    def test_missing_params(self):
        # NOTE: Request with 'game_id' missing from params
        response = self.post({
            'user_id': 'someuser',
            'move': 'd4'
        })
        self.assertEqual(response.status_code, 400)

    def test_correct_params(self):
        # NOTE: Request with all required params
        response = self.post({
            'user_id': 'someuser',
            'move': 'Qxe6',
            'game_id': 'somegame'
        })
        self.assertEqual(response.status_code, 200)
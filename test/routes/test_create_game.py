"""Test cases for the POST server route /creategame."""

import unittest
from server.server import app

class CreateGameTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/creategame'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /creategame?param_1=1&param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return CreateGameTest.client.post(CreateGameTest.route, data=data)

    # TODO: Tests
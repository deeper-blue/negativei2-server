"""Test cases for the GET server route /getgame."""

import unittest
from server.server import app

class GetGameTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/getgame'
        cls.client = app.test_client()

    def get(self, subroute):
        """Helper function for making GET requests.

        Usage:
            # GET /getgame/1
            response = self.get('/1')
        """
        return GetGameTest.client.get(GetGameTest.route + subroute)

    # TODO: Tests
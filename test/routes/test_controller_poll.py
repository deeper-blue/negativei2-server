"""Test cases for the GET server route /controllerpoll."""

import unittest
from server.server import app

class ControllerPollTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(self):
        """Runs once before all test cases."""
        cls.route = '/controllerpoll'
        cls.client = app.test_client()

    def get(self, subroute):
        """Helper function for making GET requests.

        Usage:
            # GET /controllerpoll/1
            response = self.get('/1')
        """
        return ControllerPollTest.client.get(ControllerPollTest.route + subroute)

    # TODO: Tests
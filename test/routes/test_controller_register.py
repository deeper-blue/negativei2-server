"""Test cases for the POST server route /controllerregister."""

import unittest
from server.server import app

class ControllerRegisterTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/controllerregister'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /controllerregister?param_1=1&param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return ControllerRegisterTest.client.post(ControllerRegisterTest.route, data=data)

    # TODO: Tests
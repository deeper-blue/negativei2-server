"""Test cases for the POST server route /controllerregister."""

import unittest
from unittest.mock import patch
from server.server import app
from server.schemas.controller import CONTROLLER_COLLECTION, TIMEOUT
from .mock_firebase import MockClient

OK = 200
BAD_REQUEST = 400

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
            # POST /controllerregister -F "param_1=1&param_2=2"
            response = self.post({param_1: 1, param_2: 2})
        """
        return ControllerRegisterTest.client.post(self.route, data=data)

    def set_up_mock_db(self, mock_db):
        "Creates some entries in the mock database"
        pass

    @patch('server.server.db', new_callable=MockClient)
    def test_new_controller_can_register(self, mock_db):
        "Tests that a controller can register if not seen before"
        controller_id = "kevin"
        params = {"board_id": controller_id,
                  "board_version": "0.0.1"}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        # assert that controller is in database
        self.assertTrue(mock_db.collection(CONTROLLER_COLLECTION).document(controller_id).exists)

    @patch('server.server.db', new_callable=MockClient)
    def test_controller_cant_register_twice(self, mock_db):
        "Tests that a controller can't register within the time-out window"
        params = {"board_id": "kevin",
                  "board_version": "0.0.1"}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_controller_can_re_register_after_time_out(self, mock_db):
        "Test controller can re-register after time-out"
        controller_id = "kevin"
        params = {"board_id": controller_id,
                  "board_version": "0.0.1"}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        # make sure at least TIMEOUT seconds have "passed"
        mock_db.collection(CONTROLLER_COLLECTION).document(controller_id).data["last_seen"] -= 2*TIMEOUT
        response = self.post(params)
        self.assertEqual(OK, response.status_code)

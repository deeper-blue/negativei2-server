"""Test cases for the POST server route /creategame."""

import time
import json
import unittest
import pytest
from unittest.mock import patch
from server.server import app
from server.game import WHITE, BLACK
from server.schemas.controller import TIMEOUT
from .mock_firebase import MockClient, MockAuth

OK          = 200
BAD_REQUEST = 400

@patch('firebase_admin.auth', new_callable=MockAuth)
@patch('server.server.db', new_callable=MockClient)
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
            # POST /creategame -F param_1=1 -F param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return CreateGameTest.client.post(self.route, data=data)

    def create_dummy_params(self):
        """Helper method to create dummy parameters for /creategame"""
        return {"creator_id": "some_creator",
                "player1_id": "OPEN", # TODO: make a constant in the file that deals with this and import it
                "player2_id": "OPEN",
                "time_per_player": 60 * 60, # 1 hour per player
                "board_id": 'kevin',
                "public": True}

    def set_up_mock(self, mock_db, mock_auth):
        """Creates some entries in the mock database"""
        mock_auth._mock_add_user("some_creator")
        mock_db.collection("counts").add({'count': 0}, document_id='games')
        mock_db.collection("controllers").add({'board_id': 'kevin',
                                               'board_version': '1.0',
                                               'game_id': None,
                                               'last_ply_count': 0,
                                               'last_seen': time.time()}, document_id='kevin')
        mock_db.collection("controllers").add({'board_id': 'offline',
                                               'board_version': '1.0',
                                               'game_id': None,
                                               'last_ply_count': 0,
                                               'last_seen': time.time() - 2*TIMEOUT},
                                              document_id='offline')

    def test_invalid_creator_id(self, mock_db, mock_auth):
        """An invalid creator ID should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["creator_id"] = "definitelyinvalidID"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_invalid_player_id(self, mock_db, mock_auth):
        """An invalid player ID should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["player1_id"] = "definitelyinvalidID"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_two_ais(self, mock_db, mock_auth):
        """Two AI slots should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["player1_id"] = "AI"
        params["player2_id"] = "AI"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_negative_time_per_player(self, mock_db, mock_auth):
        """Having negative time_per_player should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["time_per_player"] = -500
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_controller_id_not_exist(self, mock_db, mock_auth):
        """If a controller doesn't exist, then it should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params['board_id'] = 'invalid_board'
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_controller_offline(self, mock_db, mock_auth):
        """If a controller hasn't polled since timeout, then it should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params['board_id'] = 'offline'
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_create_game_object_sensible(self, mock_db, mock_auth):
        """The fields in the returned object have some values
           that need to be there.
        """
        self.set_up_mock(mock_db, mock_auth)

        params = self.create_dummy_params()
        response = self.post(params)
        json_game = json.loads(response.data)

        # check times
        time = params["time_per_player"]
        self.assertEqual(time, json_game["time_controls"])
        self.assertEqual(time, json_game["remaining_time"][WHITE])
        self.assertEqual(time, json_game["remaining_time"][BLACK])

        # check in progress
        self.assertTrue(json_game["in_progress"])
        self.assertFalse(json_game["game_over"]["game_over"])

        # check move count
        self.assertEqual(1, json_game["move_count"])
        self.assertEqual(0, json_game["ply_count"])

        # check history
        self.assertListEqual([], json_game["history"])

    def test_controller_assigned(self, mock_db, mock_auth):
        """The controller document should have the new game ID"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)

        json_game = json.loads(response.data)
        game_id = json_game['id']

        controller_dict = mock_db.collection("controllers").document(params['board_id']).get().to_dict()
        self.assertEqual(game_id, controller_dict['game_id'])

    def test_create_then_get_game(self, mock_db, mock_auth):
        """Creating a game then getting the same game_id should return
           the same object.
        """
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        json_game = json.loads(response.data)
        game_id = json_game["id"]
        get_game_response = self.client.get(f"/getgame/{game_id}")
        self.assertEqual(OK, get_game_response.status_code)
        json_get_game = json.loads(get_game_response.data)
        self.assertDictEqual(json_get_game, json_game)

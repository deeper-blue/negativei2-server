"""Test cases for the POST server route /creategame."""

import json
import unittest
import pytest
from unittest.mock import patch
from server.server import app
from server.game import WHITE, BLACK
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
                "board_id": 0}

    def set_up_mock(self, mock_db, mock_auth):
        """Creates some entries in the mock database"""
        mock_auth._mock_add_user("some_creator")

    def test_invalid_creator_id(self, mock_db, mock_auth):
        """An invalid creator ID should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["creator_id"] = "definitelyinvalidID"
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_invalid_player_id(self, mock_db, mock_auth):
        """An invalid player ID should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["player1_id"] = "definitelyinvalidID"
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_negative_time_per_player(self, mock_db, mock_auth):
        """Having negative time_per_player should error"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["time_per_player"] = -500
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @pytest.mark.xfail
    def test_create_two_games_same_board_id(self, mock_db, mock_auth):
        """Creating two games that both use the same board_id should error
           Each board can only host 1 game at a time
        """
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        # create second game with same params (same board_id)
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
        print(f"json_game: {json_game}")
        print(f"Game ID: {game_id}")
        get_game_response = self.client.get(f"/getgame/{game_id}")
        self.assertEqual(OK, get_game_response.status_code)
        json_get_game = json.loads(get_game_response.data)
        self.assertDictEqual(json_get_game, json_game)

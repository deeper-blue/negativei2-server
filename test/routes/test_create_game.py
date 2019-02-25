"""Test cases for the POST server route /creategame."""

import json
import unittest
from unittest.mock import patch
from server.server import app
from server.game import WHITE, BLACK
from .mock_firebase import MockClient

OK          = 200
BAD_REQUEST = 400

class CreateGameTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/creategame'
        cls.client = app.test_client()

    def post(self, data):
        # TODO: find out if below actually uses URL params or POST params as should
        """Helper function for making POST requests.

        Usage:
            # POST /creategame?param_1=1&param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return CreateGameTest.client.post(self.route, data=data)

    def create_dummy_params(self):
        """Helper method to create dummy parameters for /creategame"""
        return {"creator_id": "some_creator", # TODO: maybe create a dummy player in Firebase?
                "player1_id": "OPEN", # TODO: make a constant in the file that deals with this and import it
                "player2_id": "OPEN",
                "time_per_player": 60 * 60, # 1 hour per player
                "board_id": 0}

    @patch('server.server.db', new_callable=MockClient)
    def test_invalid_creator_id(self, mock_db):
        """An invalid creator ID should error"""
        params = self.create_dummy_params()
        params["creator_id"] = "definitelyinvalidID"
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_invalid_player_id(self, mock_db):
        """An invalid player ID should error"""
        params = self.create_dummy_params()
        params["player1_id"] = "definitelyinvalidID"
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_negative_time_per_player(self, mock_db):
        """Having negative time_per_player should error"""
        params = self.create_dummy_params()
        params["time_per_player"] = -500
        response = self.post(params)
        print(response)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_create_two_games_same_board_id(self, mock_db):
        """Creating two games that both use the same board_id should error
           Each board can only host 1 game at a time
        """
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        # create second game with same params (same board_id)
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_create_game_object_sensible(self, mock_db):
        """The fields in the returned object have some values
           that need to be there.
        """
        params = self.create_dummy_params()
        response = self.post(params)
        json_game = json.loads(response.data)

        # check times
        time = params["time_per_player"]
        self.assertEquals(time, json_game["time_controls"])
        self.assertEquals(time, json_game["remaining_time"][WHITE])
        self.assertEquals(time, json_game["remaining_time"][BLACK])

        # check in progress
        self.assertTrue(json_game["in_progress"])
        self.assertFalse(json_game["game_over"])

        # check move count
        self.assertEqual(0, json_game["move_count"])
        self.assertEqual(0, json_game["ply_count"])

        # check history
        self.asserListEqual([], json_game["history"])

    @patch('server.server.db', new_callable=MockClient)
    def test_create_then_get_game(self, mock_db):
        """Creating a game then getting the same game_id should return
           the same object.
        """
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        json_game = json.loads(response.data)
        game_id = json_game["game_id"]
        get_game_respone = self.client.get(f"/getgame/{game_id}")
        self.assertEqual(OK, get_game_response.status_code)
        json_get_game = json.loads(get_game_response.data)
        self.assertDictEqual(json_get_game, json_game)

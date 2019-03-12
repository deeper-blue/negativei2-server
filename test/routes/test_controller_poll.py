"""Test cases for the GET server route /controllerpoll."""

import time
import json
import unittest
from unittest.mock import patch
from server.server import app
from server.schemas.controller import CONTROLLER_COLLECTION, TIMEOUT
from .mock_firebase import MockClient

OK = 200
BAD_REQUEST = 400
NO_HISTORY = {"creator": "some_creator",
              "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
              "free_slots": 2,
              "game_over": {"game_over":False,"reason":None},
              "history": [],
              "id": "no_history",
              "in_progress": True,
              "move_count": 1,
              "pgn": "",
              "players": {"b":None,"w":None},
              "ply_count": 0,
              "remaining_time": {"b":3600,"w":3600},
              "result": "*",
              "time_controls": 3600,
              "turn": "w",
              "resigned": {"w": False, "b": False},
              "draw_offers": {
                  "w": {"made": False, "accepted": False},
                  "b": {"made": False, "accepted": False}
              }
             }

TWO_MOVES = {"creator": "some_creator",
             "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
             "free_slots": 2,
             "game_over": {"game_over":False,"reason":None},
             "history": [
                 # In theory /controllerpoll doesn't care about the moves
                 {"some_move": "wow"},
                 {"some_move": "wow"}
             ],
             "id": "two_moves",
             "in_progress": True,
             "move_count": 1,
             "pgn": "",
             "players": {"b":None,"w":None},
             "ply_count": 2,
             "remaining_time": {"b":3600,"w":3600},
             "result": "*",
             "time_controls": 3600,
             "turn": "w",
             "resigned": {"w": False, "b": False},
             "draw_offers": {
                 "w": {"made": False, "accepted": False},
                 "b": {"made": False, "accepted": False}
             }
            }

class ControllerPollTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/controllerpoll'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /controllerregister -F "param_1=1&param_2=2"
            response = self.post({param_1: 1, param_2: 2})
        """
        return self.client.post(self.route, data=data)

    def set_up_mock_db(self, mock_db):
        """Helper function to populate db"""
        kevin = {"board_id": "kevin", "board_version": "0.0.1",
                 "last_seen": time.time(), "game_id": None}
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").set(kevin)
        mock_db.collection("games").document("no_history").set(NO_HISTORY)
        mock_db.collection("games").document("two_moves").set(TWO_MOVES)

    @patch('server.server.db', new_callable=MockClient)
    def test_return_empty_if_no_assigned_game(self, mock_db):
        """If there is no assigned game to the controller, there should be nothing to do"""
        self.set_up_mock_db(mock_db)
        params = {"board_id": "kevin", "ply_count": 0, "error": None}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        response_json = json.loads(response.data)
        self.assertEqual(0, len(response_json["history"]))

    @patch('server.server.db', new_callable=MockClient)
    def test_return_empty_if_no_history(self, mock_db):
        """Should return no moves if game has no moves"""
        self.set_up_mock_db(mock_db)
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").data["game_id"] = "no_history"
        params = {"board_id": "kevin", "ply_count": 0, "error": None}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        response_json = json.loads(response.data)
        self.assertEqual(0, len(response_json["history"]))

    @patch('server.server.db', new_callable=MockClient)
    def test_return_all_history_if_ply_0(self, mock_db):
        """Should return the whole history if a game has 0 moves"""
        self.set_up_mock_db(mock_db)
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").data["game_id"] = "two_moves"
        params = {"board_id": "kevin", "ply_count": 0, "error": None}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        response_json = json.loads(response.data)
        self.assertEqual(2, len(response_json["history"]))

    @patch('server.server.db', new_callable=MockClient)
    def test_should_return_partial_history_if_ply_nonzero(self, mock_db):
        """Should only return moves after ply"""
        self.set_up_mock_db(mock_db)
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").data["game_id"] = "two_moves"
        params = {"board_id": "kevin", "ply_count": 1, "error": None}
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        response_json = json.loads(response.data)
        self.assertEqual(1, len(response_json["history"]))

    @patch('server.server.db', new_callable=MockClient)
    def test_return_nothing_when_error(self, mock_db):
        """When the controller reports an error, the server should return nothing"""
        self.set_up_mock_db(mock_db)
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").data["game_id"] = "two_moves"
        params = {"board_id": "kevin", "ply_count": 1, "error": 1}
        response = self.post(params)
        print(response.data)
        self.assertEqual(OK, response.status_code)
        response_json = json.loads(response.data)
        self.assertEqual(0, len(response_json["history"]))

    @patch('server.server.db', new_callable=MockClient)
    def test_unknown_controller_errors(self, mock_db):
        """If the controller is not registered, should error"""
        self.set_up_mock_db(mock_db)
        params = {"board_id": "unknown_board", "ply_count": 0, "error": None}
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    @patch('server.server.db', new_callable=MockClient)
    def test_registration_time_out_errors(self, mock_db):
        """If the controller has not been seen in TIME_OUT seconds, should error"""
        self.set_up_mock_db(mock_db)
        mock_db.collection(CONTROLLER_COLLECTION).document("kevin").data["last_seen"] -= 2*TIMEOUT
        params = {"board_id": "kevin", "ply_count": 0, "error": None}
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

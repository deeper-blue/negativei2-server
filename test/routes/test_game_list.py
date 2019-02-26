"""Test cases for the POST server route /gamelist."""

import json
import copy
import unittest
from unittest.mock import patch
from server.server import app
from server.server import GAMES_COLLECTION
from .mock_firebase import MockClient

OK = 200

TWO_FREE_SLOTS = {"creator": "some_creator",
                  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                  "free_slots": 2,
                  "game_over": {"game_over":False,"reason":None},
                  "history": [],
                  "id": "D27Izb98SA1znYVgGKPn",
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

class GameListTest(unittest.TestCase):
    # Setup and helper functions

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases."""
        cls.route = '/gamelist'
        cls.client = app.test_client()

    def get(self):
        """Helper function for making GET requests.

        Usage:
            # GET /gamelist
            response = self.get()
        """
        return self.client.get(self.route)

    @patch('server.server.db', new_callable=MockClient)
    def test_single_in_progress_with_open_slots(self, mock_db):
        """A game that is in progress with open slots should be returned"""
        mock_db.collection(GAMES_COLLECTION).add(copy.deepcopy(TWO_FREE_SLOTS))
        response = self.get()
        self.assertEqual(OK, response.status_code)
        game_list = json.loads(response.data)
        self.assertEqual(1, len(game_list))
        self.assertDictEqual(TWO_FREE_SLOTS, game_list[0])

    @patch('server.server.db', new_callable=MockClient)
    def test_finished_not_returned(self, mock_db):
        """A game that is finished should not be returned"""
        finished = copy.deepcopy(TWO_FREE_SLOTS)
        finished["game_over"]["game_over"] = True
        finished["game_over"]["reason"] = "Three-fold repetition"
        mock_db.collection(GAMES_COLLECTION).add(finished)
        response = self.get()
        self.assertEqual(OK, response.status_code)
        game_list = json.loads(response.data)
        self.assertEqual(0, len(game_list))

    @patch('server.server.db', new_callable=MockClient)
    def test_no_open_slots_not_returned(self, mock_db):
        """A game that has no open slots should not be returned"""
        closed = copy.deepcopy(TWO_FREE_SLOTS)
        closed["players"]["b"] = "player_id"
        closed["players"]["w"] = "player2_id"
        closed["free_slots"] = 0
        mock_db.collection(GAMES_COLLECTION).add(closed)
        response = self.get()
        self.assertEqual(OK, response.status_code)
        game_list = json.loads(response.data)
        self.assertEqual(0, len(game_list))

    @patch('server.server.db', new_callable=MockClient)
    def test_no_games_nothing_returned(self, mock_db):
        """Nothing should be returned if there are no games in the database"""
        response = self.get()
        self.assertEqual(OK, response.status_code)
        game_list = json.loads(response.data)
        self.assertEqual(0, len(game_list))

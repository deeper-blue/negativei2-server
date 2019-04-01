import copy
import unittest
from unittest.mock import patch
from server.server import app
from server.server import GAMES_COLLECTION
from .mock_firebase import MockClient, MockAuth

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
                  "public": True,
                  "ply_count": 0,
                  "remaining_time": {"b":3600,"w":3600},
                  "result": "*",
                  "time_controls": 3600,
                  "turn": "w",
                  "resigned": {"w": False, "b": False},
                  "draw_offers": {
                      "w": {"made": False, "accepted": False},
                      "b": {"made": False, "accepted": False}
                  },
                  'initial_positions': {'a1': 'a1', 'a2': 'a2', 'a7': 'a7', 'a8': 'a8', 'b1': 'b1', 'b2': 'b2', 'b7': 'b7', 'b8': 'b8', 'c1': 'c1', 'c2': 'c2', 'c7': 'c7', 'c8': 'c8', 'd1': 'd1', 'd2': 'd2', 'd7': 'd7', 'd8': 'd8', 'e1': 'e1', 'e2': 'e2', 'e7': 'e7', 'e8': 'e8', 'f1': 'f1', 'f2': 'f2', 'f7': 'f7', 'f8': 'f8', 'g1': 'g1', 'g2': 'g2', 'g7': 'g7', 'g8': 'g8', 'h1': 'h1', 'h2': 'h2', 'h7': 'h7', 'h8': 'h8'}
                 }

OK = 200
BAD_REQUEST = 400

@patch('firebase_admin.auth', new_callable=MockAuth)
@patch('server.server.db', new_callable=MockClient)
class JoinGameTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before all test cases"""
        cls.route = '/joingame'
        cls.client = app.test_client()

    def post(self, data):
        """Helper function for making POST requests.

        Usage:
            # POST /creategame -F param_1=1 -F param_2=2
            response = self.post({param_1: 1, param_2: 2})
        """
        return self.client.post(self.route, data=data)

    def set_up_mock(self, mock_db, mock_auth):
        mock_db.collection(GAMES_COLLECTION).add(TWO_FREE_SLOTS, document_id="two_free_slots")
        mock_auth._mock_add_user("new_player")
        mock_auth._mock_add_user("player1")
        mock_auth._mock_add_user("player2")
        mock_auth._mock_add_user("some_creator")

        full_player_ids = copy.deepcopy(TWO_FREE_SLOTS)
        full_player_ids["players"]["w"] = "player1"
        full_player_ids["players"]["b"] = "player2"
        mock_db.collection(GAMES_COLLECTION).add(full_player_ids, document_id="full_player_ids")

        full_ai = copy.deepcopy(TWO_FREE_SLOTS)
        full_ai["players"]["w"] = "AI"
        full_ai["players"]["b"] = "AI"
        mock_db.collection(GAMES_COLLECTION).add(full_ai, document_id="full_ai")

    def create_dummy_params(self):
        """Helper method to create dummy parameters for /joingame"""
        return {"game_id": "two_free_slots",
                "player_id": "new_player",
                "side": "w"}

    def test_join_as_white(self, mock_db, mock_auth):
        """Should be able to join a game with a free white slot as white"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        game = mock_db.collection(GAMES_COLLECTION).document("two_free_slots").get().to_dict()
        self.assertEqual("new_player", game["players"]["w"])

    def test_join_as_black(self, mock_db, mock_auth):
        """Should be able to join a game with a free black slot as black"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["side"] = "b"
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        game = mock_db.collection(GAMES_COLLECTION).document("two_free_slots").get().to_dict()
        self.assertEqual("new_player", game["players"]["b"])

    def test_join_slot_contains_player_id(self, mock_db, mock_auth):
        """Should not be able to join a game when requested slot full"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["game_id"] = "full_player_ids"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_join_slot_contains_ai(self, mock_db, mock_auth):
        """Should not be able to join a game when requested slot full"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["game_id"] = "full_ai"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_join_slot_invalid_player_id(self, mock_db, mock_auth):
        """Should not be able to join a game when not valid player ID"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["player_id"] = "invalid_player_id"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_join_slot_invalid_game_id(self, mock_db, mock_auth):
        """Should not be able to join a game when not valid game ID"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        params["game_id"] = "invalid_game_id"
        response = self.post(params)
        self.assertEqual(BAD_REQUEST, response.status_code)

    def test_side_not_provided(self, mock_db, mock_auth):
        """Should be able to join a game without providing a side to join"""
        self.set_up_mock(mock_db, mock_auth)
        params = self.create_dummy_params()
        del params["side"]
        response = self.post(params)
        self.assertEqual(OK, response.status_code)
        game = mock_db.collection(GAMES_COLLECTION).document("two_free_slots").get().to_dict()
        player_id_added = game["players"]["w"] == "new_player" or game["players"]["b"] == "new_player"
        self.assertTrue(player_id_added)

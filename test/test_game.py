import unittest
from server.server import app

class GameTest(unittest.TestCase):
    def test_make_move_missing_params(self):
        c = app.test_client()
        missing_param_data = {'user_id': 'someuser',
                              'move': 'E2 to D3'
                              # note, missing game_id
                             }
        response = c.post('/makemove', data=missing_param_data)
        self.assertEqual(response.status_code, 400)

    def test_make_move_correct_params(self):
        c = app.test_client()
        correct_param_data = {'user_id': 'someuser',
                              'move': 'E2 to D3',
                              'game_id': 'somegame'
                             }
        response = c.post('/makemove', data=correct_param_data)
        self.assertEqual(response.status_code, 200)

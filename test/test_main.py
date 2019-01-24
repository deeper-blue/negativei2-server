import unittest
from server.server import main

class MainTest(unittest.TestCase):
    def test_example(self):
        self.assertEqual(main(), 'hello world')

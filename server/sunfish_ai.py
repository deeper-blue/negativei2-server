"""Interface to the Sunfish chess engine."""
from sunfish.tools import parseFEN, renderSAN
from sunfish.sunfish import Searcher

def get_ai_move(board):
    """Given a python-chess Board, produce a move.

    This is the main entry point to using Sunfish as an AI.
    @return A move in SAN
    """
    fen = board.fen()
    position = parseFEN(fen)
    searcher = Searcher()
    move, _ = searcher.search(position, secs=2)
    return renderSAN(position, move)

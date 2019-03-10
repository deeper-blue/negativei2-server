import chess
import chess.pgn

WHITE = 'w'
BLACK = 'b'

SCORES = {
    WHITE: '1-0',
    BLACK: '0-1',
    'draw': '1/2-1/2'
}

class Game:
    """Class representing and encapsulating the logic required for handling a chess game with time controls.

    Internal attributes (Do not modify or access directly):
        _id:             The assigned ID of the Game object (not the Python-assigned one).
        _creator:        The ID of the user that created the game.
        _time_controls:  The time controls for the game (starting time for each side) in seconds.
        _remaining_time: The remaining time for both sides.
        _board:          The internal board object for the game.
        _players:        The sides of the game and their corresponding players.
        _plies:          The ply count (version number).
        _history:        The game move history.
        _resigned:       The resignation status for both sides.
        _draw_offers:    The draw offer status for both sides.
            MEANING:
                _draw_offers[WHITE]['made']     represents whether white has made a draw offer or not.
                _draw_offers[WHITE]['accepted'] represents whether white's draw offer had been accepted by black.
                                                and vice-versa for black.

    Properties:
        The internal attributes listed above can be accessed through properties defined in this class.
        There are additional properties defined for other information that is relevant to the Game object
        and each of these properties has their own docstring description.

    Functions:
        Any modifications to attributes (which are intended to be modified) can be done through instance
        methods provided in the class. Each of these instance methods has their own docstring description.
    """

    def __init__(self, creator_id, game_id=None, time_controls=None):
        if isinstance(creator_id, str):
            self._creator = creator_id
        else:
            raise TypeError(f"Expected 'creator_id' to be a string, got: {type(creator_id)}.")

        if isinstance(game_id, str):
            self._id = game_id
        elif game_id is None:
            self._id = game_id
        else:
            raise TypeError(f"Expected 'game_id' argument to be a str (or None), got: {type(game_id)}.")

        if isinstance(time_controls, int):
            if time_controls < 0:
                raise ValueError(f"Cannot create a game with negative time: {time_controls}.")
            else:
                self._time_controls = time_controls
        elif time_controls is None:
            self._time_controls = time_controls
        else:
            raise TypeError(f"Expected 'time_controls' argument to be an int (or None), got: {type(time_controls)}.")

        self._remaining_time = {WHITE: time_controls, BLACK: time_controls}
        self._board = chess.Board()
        self._players = {WHITE: None, BLACK: None}
        self._plies = 0
        self._history = []
        self._resigned = {WHITE: False, BLACK: False}
        self._draw_offers = {
            WHITE: {'made': False, 'accepted': False},
            BLACK: {'made': False, 'accepted': False}
        }

    @property
    def id(self) -> str:
        """The game ID"""
        return self._id

    @property
    def creator(self) -> str:
        """The creator's ID"""
        return self._creator

    @property
    def board(self) -> chess.Board:
        """The internal chessboard object."""
        return self._board

    @property
    def players(self) -> dict:
        """Dictionary representing the players playing the game."""
        return self._players

    @property
    def time_controls(self) -> int:
        """The time controls for the game (seconds per side at the start)."""
        return self._time_controls

    @property
    def remaining_time(self) -> int:
        """The remaining time for each player."""
        return self._remaining_time

    @property
    def ply_count(self) -> int:
        """The ply count (Total number of half-moves).

        https://en.wikipedia.org/wiki/Ply_(game_theory)
        This may also be used as the version number, as it increments with each board change (player's move).
        """
        return self._plies

    @property
    def move_count(self) -> int:
        """The full-move number (incremented after each time black moves)."""
        return self._board.fullmove_number

    @property
    def fen(self) -> str:
        """The FEN string representing the current board state."""
        return self._board.fen()

    @property
    def pgn(self) -> str:
        """The PGN string representing the game move history."""
        return chess.Board().variation_san(self._board.move_stack)

    @property
    def history(self) -> list:
        """Game move history (list of extended move descriptions)."""
        return self._history

    @property
    def turn(self) -> str:
        """The current side to move ('w' or 'b')."""
        return WHITE if self._board.turn else BLACK

    @property
    def free_slots(self) -> int:
        """The number of open slots for the game."""
        return sum([1 if player is None else 0 for player in self.players.values()])

    @property
    def resigned(self) -> dict:
        """The resignation status for both sides."""
        return self._resigned

    @property
    def draw_offers(self) -> dict:
        """The draw offer status for both sides."""
        return self._draw_offers

    @property
    def result(self) -> str:
        """The game result (1-0, 0-1, 1/2-1/2, or * if the game is in progress)."""

        # Always claim a draw when possible (By three-fold repetition or fifty-move rule)
        result = self._board.result(claim_draw=True)

        # Override result to black win if white resigns
        if self._resigned[WHITE]:
            result = SCORES[BLACK]

        # Override result to white win if black resigns
        if self._resigned[BLACK]:
            result = SCORES[WHITE]

        # Override result to draw if either side accepts a draw
        if self._draw_offers[WHITE]['accepted'] or self._draw_offers[BLACK]['accepted']:
            result = SCORES['draw']

        # Override result to black win if white has no time
        if self._remaining_time[WHITE] == 0:
            result = SCORES[BLACK]

        # Override result to white win if black has no time
        if self._remaining_time[BLACK] == 0:
            result = SCORES[WHITE]

        # Override result to draw if both sides have no time (this should never occur, but just in case)
        if (self._remaining_time[WHITE] == 0) and (self._remaining_time[BLACK] == 0):
            result = SCORES['draw']

        return result

    @property
    def in_progress(self) -> bool:
        """Whether the game is in progress, or has ended."""
        return self.result == '*'

    @property
    def game_over(self) -> dict:
        """The game-over status (and game-over reason if the game is over)."""

        # Always claim a draw when possible (By three-fold repetition or fifty-move rule)
        if self._board.is_game_over(claim_draw=True):
            if self._board.can_claim_threefold_repetition():
                reason = 'Three-fold repetition'
            if self._board.can_claim_fifty_moves():
                reason = 'Fifty move rule'
            if self._board.is_seventyfive_moves():
                reason = 'Seventy-five move rule'
            if self._board.is_insufficient_material():
                reason = 'Insufficient material'
            if self._board.is_checkmate():
                reason = 'Checkmate'
            if self._board.is_stalemate():
                reason = 'Stalemate'
            if self._board.is_fivefold_repetition():
                reason = 'Five-fold repetition'

            return {'game_over': True, 'reason': reason}

        # Check for resignation
        if self._resigned[WHITE] or self._resigned[BLACK]:
            return {'game_over': True, 'reason': 'Resignation'}

        # Check for accepted draw offers
        if self._draw_offers[WHITE]['accepted'] or self._draw_offers[BLACK]['accepted']:
            return {'game_over': True, 'reason': 'Draw by agreement'}

        # Time as a game-over reason should take more priority over the other reasons
        if (self._remaining_time[WHITE] == 0) or (self._remaining_time[BLACK] == 0):
            return {'game_over': True, 'reason': 'Time'}

        # If none of the above, then the game is not over
        return {'game_over': False, 'reason': None}

    def _construct_move_description(self, move) -> dict:
        """Constructs an extended move description for a single move, detailing all necessary information about the move.

        NOTE: This function must be called directly after the move to be described has actually been made.
            This is because it relies on move stack manipulation to work; the function temporarily pops the move
            from the move stack whilst constructing the description, then re-pushes the move onto the move stack.

        Arguments:
            move: The requested move (chess.Move object).
        Returns:
            Extended move description, detailing all necessary and relevant information regarding the move.
        """

        # Check that the provided move is actually on the top of the move stack
        if self._board.peek() != move:
            raise ValueError(f"Expected move '{move}' to be on the top of move stack, got: '{self._board.peek()}'.")

        # Temporarily pop the move from the move stack (in order to construct the extended move description)
        self._board.pop()

        # Construct the extended move description
        description = {
            'side': self.turn,
            'ply_count': self.ply_count,
            'move_count': self.move_count,
            'piece': self._board.piece_at(move.from_square).symbol().lower(),
            'from': chess.square_name(move.from_square),
            'to': chess.square_name(move.to_square),
            'promotion': {
                'promotion': False if move.promotion is None else True,
                'piece': None
            },
            'capture': {
                'capture': self._board.is_capture(move),
                'piece': None
            },
            'castle': {
                'castle': self._board.is_castling(move),
                'side': None
            },
            'en_passant': {
                'en_passant': self._board.is_en_passant(move),
                'square': None
            }
        }

        # Update the promotion piece if promotion took place
        if description['promotion']['promotion']:
            description['promotion']['piece'] = chess.PIECE_SYMBOLS[move.promotion].lower()

        # Update the capture piece and en-passant square value to account for en-passant capture
        if description['capture']['capture']:
            if description['en_passant']['en_passant']:
                # NOTE: The 'down' shift performed below to get the square behind the en-passant square comes from:
                # https://github.com/niklasf/python-chess/blob/102ca5d89e23d5bb9413fb384a78ac4eb4f48bf9/chess/__init__.py#L1963
                down = -8 if self.turn == WHITE else 8
                description['en_passant']['square'] = chess.square_name(self._board.ep_square + down)
                description['capture']['piece'] = 'p' # Always capturing a pawn
            else:
                description['capture']['piece'] = self._board.piece_at(move.to_square).symbol().lower()

        # Update the castling side value if castling took place
        if description['castle']['castle']:
            if self._board.is_kingside_castling(move):
                description['castle']['side'] = 'k'
            elif self._board.is_queenside_castling(move):
                description['castle']['side'] = 'q'

        # Re-push the move back on the move stack
        self._board.push(move)

        return description

    def _invert(self, color) -> str:
        """Inverts 'w' or 'b'."""
        if color not in (WHITE, BLACK):
            raise ValueError(f"Invalid color '{color}': expected one of ('w', 'b').")
        else:
            return BLACK if color == WHITE else WHITE

    def move(self, san) -> dict:
        """Makes a requested move on the internal board.

        Arguments:
            san: The requested move (in Standard Algebraic Notation).
        Returns:
            Detailed description (in dictionary form) representing the move that was made.
        Raises:
            ValueError: When the given move is invalid SAN (in the current game context).
        """

        # Prevent a move from being made if the game is over
        if not self.in_progress:
            raise RuntimeError(f"Cannot make move '{san}' for side '{self.turn}' in ended game.")

        # Check if the side has a player assigned to it
        if self.players[self.turn] is None:
            raise RuntimeError(f"Cannot make move '{san}' for side '{self.turn}': No player found.")

        # Make the move on the internal board
        # NOTE: At this point, self._board.push_san() raises a ValueError if the SAN is invalid in the current context.
        move = self._board.push_san(san)

        # Increment ply count after move is successfully made
        self._plies += 1

        # Clear any draw offers made by either player
        for side in (WHITE, BLACK):
            self.decline_draw(side=side)

        # Construct the extended move description (adding a SAN field)
        # HACK: For logical purposes, it makes most sense for the SAN notation of the move
        #   to be at the start of the detailed move dict (despite dicts not actually being ordered)
        #   this was the cleanest way I could find to do it - just merging two dicts together.
        detailed_move = {**{'san': san}, **self._construct_move_description(move)}

        # Add the detailed move to self._history
        self._history.append(detailed_move)

        return detailed_move

    def add_player(self, id_, side) -> None:
        """Adds a player to the current game.

        Arguments:
            id_: The player's ID.
            side: The side the player should be assigned to. ('w' or 'b')
        """

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")
        if not isinstance(id_, str):
            raise TypeError(f"Expected 'id_' argument to be a string, got: {type(id_)}.")
        if self._players[self._invert(side)] == id_:
            raise RuntimeError(f"Cannot have the same ID '{id_}' as player on other side '{self._invert(side)}'.")
        if self._players[side] is None:
            self._players[side] = id_
        else:
            raise RuntimeError(f"Player slot for side '{side}' is already occupied.")

    def time_delta(self, delta, side=None) -> None:
        """Apply a time (in seconds) increment or decrement to a side's time counter.

        Arguments:
            delta: The number of seconds to increment or decrement a side's time counter by.
                - Time decrements should be a negative integer.
                - Time increments should be a positive integer.
            side: The side to apply the time delta to. Expects:
                - 'w' or 'b'
                - None (will automatically select whichever side's turn it currently is)
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")
        if not isinstance(delta, int):
            raise TypeError(f"Expected 'delta' argument to be an int, got: {type(delta)}.")

        # Don't apply delta if there are no time controls
        if self._time_controls is None:
            return

        # Don't apply delta if the game is over
        if not self.in_progress:
            return

        # Don't apply delta if side has no seconds left
        if self._remaining_time[side] == 0:
            return

        # If decrement would set time below 0, don't allow it (reset time to 0)
        if (delta < 0) and (self._remaining_time[side] + delta < 0):
            self._remaining_time[side] = 0
            return

        # Apply the time delta
        self._remaining_time[side] += delta

    def resign(self, side=None) -> None:
        """Resigns the game for a side.

        Arguments:
            side: The side to resign. Expects:
                - 'w' or 'b'
                - None (will automatically select whichever side's turn it currently is)
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")

        # If game is already over, don't do anything
        if not self.in_progress:
            return

        # If player is already resigned, don't do anything
        if self._resigned[side]:
            return

        # Resign
        self._resigned[side] = True

    def offer_draw(self, side=None) -> None:
        """Offer a draw to the other side.

        Arguments:
            side: The side offering the draw.
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")

        # Don't allow draw offering if the game is not in progress
        if not self.in_progress:
            return

        # If draw offer is already made, don't do anything
        if self._draw_offers[side]['made']:
            return

        # If the opponent has offered a draw, accept it
        if self._draw_offers[self._invert(side)]['made']:
            self.accept_draw(side=side)

        # Offer the draw
        self._draw_offers[side]['made'] = True

    def accept_draw(self, side=None) -> None:
        """Accept a draw offer made by the other side.

        Arguments:
            side: The side accepting the draw.
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")

        # Don't allow draw accepting if the game is not in progress
        if not self.in_progress:
            return

        # Don't allow draw accepting if the opposite side hasn't made a draw offer
        if not self._draw_offers[self._invert(side)]['made']:
            return

        # Accept the draw made by the other side
        self._draw_offers[self._invert(side)]['accepted'] = True

    def decline_draw(self, side=None) -> None:
        """Decline a draw offer made by the other side.

        Arguments:
            side: The side declining the draw.
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")

        # Don't allow draw declining if the game is not in progress
        if not self.in_progress:
            return

        # Don't allow draw declining if the opposite side hasn't made a draw offer
        if not self._draw_offers[self._invert(side)]['made']:
            return

        # Don't allow draw declining if the offer was already accepted
        if self._draw_offers[self._invert(side)]['accepted']:
            return

        # Decline the draw made by the other side (Reset 'made' so that future draws can be offered again)
        self._draw_offers[self._invert(side)]['made'] = False

    def __str__(self) -> str:
        """String representation of the current board state.

        Builds ontop of chess.Board.__str__() to use unicode characters and add file/rank labels.

        NOTE: The piece colours will appear inverted if a light text colour is used, for example on a dark-background terminal.
        """

        output = self._board.__str__()

        # Replace white ASCII piece characters with unicode characters
        for piece in ['R', 'N', 'B', 'Q', 'K', 'P']:
            output = output.replace(piece, chess.UNICODE_PIECE_SYMBOLS[piece])

        # Replace black ASCII piece characters with unicode characters
        for piece in ['r', 'n', 'b', 'q', 'k', 'p']:
            output = output.replace(piece, chess.UNICODE_PIECE_SYMBOLS[piece])

        # Add file labels
        ranks = [f"{8-i} {rank}" for i, rank in enumerate(output.split('\n'))]

        # Add rank labels
        ranks.append('  a b c d e f g h')

        return "\n".join(ranks)

    @classmethod
    def from_create_game_schema(cls, input_dict, game_id):
        """Factory method to create a Game object from a dict validated by CreateGameInput.

        Assumes that the input dictionary has already been validated against the schema.
        """
        g = cls(input_dict['creator_id'], game_id, int(input_dict['time_per_player']))
        #TODO: below constants should be places somewhere unified
        if input_dict['player1_id'] not in ['OPEN', 'AI']:
            g.add_player(input_dict['player1_id'], 'w')
        if input_dict['player2_id'] not in ['OPEN', 'AI']:
            g.add_player(input_dict['player2_id'], 'b')

        return g

    @classmethod
    def from_dict(cls, input_dict):
        required_keys = ['id', 'creator', 'players', 'time_controls', 'history', 'remaining_time', 'ply_count', 'resigned', 'draw_offers']
        missing_keys = []

        # Check for any missing keys
        for key in required_keys:
            if key not in input_dict:
                missing_keys.append(key)

        if missing_keys:
            raise KeyError(f"Missing required attribute keys from 'input_dict': {missing_keys}")

        # Create a new game object
        game = Game(input_dict['creator'], input_dict['id'])

        # Generate a new internal board (FEN)
        game._board = chess.Board()

        # Load in necessary attributes for starting the game
        game._players = input_dict['players']
        game._time_controls = input_dict['time_controls']

        # Load in the played game moves, and replay them on the new internal board
        for move in input_dict['history']:
            game._history.append(move)
            game._board.push_san(move['san'])

        # Load in any remaining attributes from the input dictionary
        game._remaining_time = input_dict['remaining_time']
        game._plies = input_dict['ply_count']
        game._resigned = input_dict['resigned']
        game._draw_offers = input_dict['draw_offers']

        return game

    def to_dict(self) -> dict:
        """Generates a dictionary representation of the Game object, valid for flask.jsonify.

        Returns:
            Dictionary representation of the Game object.
        """

        return {
            'id':             self.id,
            'creator':        self.creator,
            'players':        self.players,
            'free_slots':     self.free_slots,
            'time_controls':  self.time_controls,
            'remaining_time': self.remaining_time,
            'resigned':       self.resigned,
            'draw_offers':    self.draw_offers,
            'in_progress':    self.in_progress,
            'result':         self.result,
            'game_over':      self.game_over,
            'turn':           self.turn,
            'ply_count':      self.ply_count,
            'move_count':     self.move_count,
            'pgn':            self.pgn,
            'history':        self.history,
            'fen':            self.fen
        }

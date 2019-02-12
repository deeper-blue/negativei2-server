import chess
import chess.pgn

WHITE = 'w'
BLACK = 'b'

class Game:
    """Class representing and encapsulating the logic required for handling a chess game with time controls.

    Internal attributes (Do not modify or access directly):
        _id:             The assigned ID of the Game object (not the Python-assigned one).
        _time_controls:  The time controls for the game (starting time for each side) in seconds.
        _remaining_time: The remaining time for both sides.
        _board:          The internal board object for the game.
        _players:        The sides of the game and their corresponding players.
        _plies:          The ply count (version number).

    Properties:
        The internal attributes listed above can be accessed through properties defined in this class.
        There are additional properties defined for other information that is relevant to the Game object
        and each of these properties has their own docstring description.

    Functions:
        Any modifications to attributes (which are intended to be modified) can be done through instance
        methods provided in the class. Each of these instance methods has their own docstring description.
    """

    def __init__(self, id, time_controls=None, fen=chess.STARTING_FEN):
        if isinstance(id, int):
            self._id = id
        else:
            raise TypeError(f"Expected 'id' argument to be an int, got: {type(id)}.")

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
        self._board = chess.Board(fen)
        self._players = {WHITE: None, BLACK: None}
        self._plies = 0

    @property
    def id(self) -> int:
        """Property for returning the game ID representing the Game object."""
        return self._id

    @property
    def board(self) -> chess.Board:
        """Property for returning the internal chessboard object."""
        return self._board

    @property
    def players(self) -> dict:
        """Property for returning a dictionary representing the players playing the game."""
        return self._players

    @property
    def time_controls(self) -> int:
        """Property for returning the time controls for the game (seconds per side at the start)."""
        return self._time_controls

    @property
    def remaining_time(self) -> int:
        """Property for returning the remaining time for each player."""
        return self._remaining_time

    @property
    def ply_count(self) -> int:
        """Property for returning the ply count (Total number of half-moves).

        https://en.wikipedia.org/wiki/Ply_(game_theory)
        This may also be used as the version number, as it increments with each board change (player's move).
        """
        return self._plies

    @property
    def move_count(self) -> int:
        """Property for returning the full-move number (incremented after each time black moves)."""
        return self._board.fullmove_number

    @property
    def fen(self) -> str:
        """Property for returning the FEN string representing the current board state."""
        return self._board.fen()

    @property
    def pgn(self) -> chess.pgn.Game:
        """Property for returning the PGN object representing the game move history.

        NOTE: Doesn't update the score field to include game-overs due to time. The move section
            of the PGN string (generated by self.moves) updates the PGN string to include this.
            This simply returns the internal PGN object - disregarding any thing to do with time controls.
        """
        return chess.pgn.Game.from_board(self._board)

    @property
    def moves(self) -> str:
        """Property for returning the moves section of the game's PGN object (as a string)."""

        # Extract the moves section of the PGN string
        moves = str(self.pgn).split("\n\n")[1]

        # Update the result field of the PGN, so it uses the actual self.result property, which
        # takes game termination due to time into consideration.
        tokens = moves.split(' ')
        tokens[-1] = self.result

        return ' '.join(tokens)

    @property
    def turn(self) -> str:
        """Property for returning the current side to move ('w' or 'b')."""
        return WHITE if self._board.turn else BLACK

    @property
    def free_slots(self) -> int:
        """Property for returning the number of open slots for the game."""
        return sum([1 if player is None else 0 for player in self.players.values()])

    @property
    def result(self) -> str:
        """Property for returning the game result (1-0, 0-1, 1/2-1/2, or * if the game is in progress)."""

        result = self._board.result()

        # Override result to black win if white has no time
        if self._remaining_time[WHITE] == 0:
            result = '0-1'

        # Override result to white win if black has no time
        if self._remaining_time[BLACK] == 0:
            result = '1-0'

        # Override result to draw if both sides have no time
        if (self._remaining_time[WHITE] == 0) and (self._remaining_time[BLACK] == 0):
            result = '1/2-1/2'

        return result

    @property
    def in_progress(self) -> bool:
        """Property for returning whether the game is in progress (true), or has ended (false)."""
        return self.result == '*'

    @property
    def game_over(self) -> dict:
        """Property for returning the game-over status (and game-over reason if the game is over)."""
        game_over = False
        reason = None

        if self._board.is_game_over():
            game_over = True

            # If the game is over for none of the other reasons, this is only remaining reason.
            # It is tricky to check for draw claims, so leave it as the default and override it.
            reason = 'Draw claimed'

            if self._board.is_seventyfive_moves():
                reason = 'Seventy-five move role'
            if self._board.is_insufficient_material():
                reason = 'Insufficient material'
            if self._board.is_checkmate():
                reason = 'Checkmate'
            if self._board.is_stalemate():
                reason = 'Stalemate'
            if self._board.is_fivefold_repetition():
                reason = 'Five-fole repetition'

        # Time as a game-over reason should take more priority over the other reasons
        if self._remaining_time[WHITE] == 0:
            # White is out of time
            game_over = True
            reason = 'Time'
        if self._remaining_time[BLACK] == 0:
            # Black is out of time
            game_over = True
            reason = 'Time'

        return {'game_over': game_over, 'reason': reason}

    def move(self, san) -> chess.Move:
        """Makes a requested move on the internal board.

        Arguments:
            san: The requested move (in Standard Algebraic Notation).
        Returns:
            Move object representing the move that was made.
        """

        # Prevent a move from being made if the game is over
        if not self.in_progress:
            raise RuntimeError(f"Cannot make move '{san}' for side '{self.turn}' in ended game.")

        # Check if the side has a player assigned to it
        if self.players[self.turn] is None:
            raise RuntimeError(f"Cannot make move '{san}' for side '{self.turn}': No player found.")

        # Make the move on the internal board
        move = self._board.push_san(san)

        # Increment ply count after move is successfully made
        self._plies += 1

        return move

    def add_player(self, id, side) -> None:
        """Adds a player to the current game.

        Arguments:
            id: The player's ID.
            side: The side the player should be assigned to. ('w' or 'b')
        """

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")
        if not isinstance(id, str):
            raise TypeError(f"Expected 'id' argument to be a string, got: {type(id)}.")
        if self._players[side] is None:
            self._players[side] = id
        else:
            raise RuntimeError(f"Player slot for side '{side}' is already occupied.")

    def time_delta(self, delta, side=None) -> None:
        """Apply a time (in seconds) increment or decrement to a side's time counter.

        Arguments:
            delta: The number of seconds to increment or decrement a side's time counter by.
                - Time decrements should be a negative integer.
                - Time increments should be a positive integer.
            side: The side to apply the time delta to ('w' or 'b').
        """

        # If no side argument given, then assume it's the current side to play
        side = side if side is not None else self.turn

        # Don't apply delta if there are no time controls
        if self._time_controls is None:
            return

        if side not in (WHITE, BLACK):
            raise ValueError(f"Invalid side '{side}': expected one of ('w', 'b').")
        if not isinstance(delta, int):
            raise TypeError(f"Expected 'delta' argument to be an int, got: {type(delta)}.")

        # Don't apply delta if side has no seconds left
        if self._remaining_time[side] == 0:
            return

        # If decrement would set time below 0, don't allow it (reset time to 0)
        if (delta < 0) and (self._remaining_time[side] + delta < 0):
            self._remaining_time[side] = 0
            return

        # Apply the time delta
        self._remaining_time[side] += delta

    def as_dict(self) -> dict:
        """Generates a dictionary representation of the Game object, valid for flask.jsonify.

        Returns:
            Dictionary representation of the Game object.
        """

        return {
            'id':             self.id,
            'players':        self.players,
            'free_slots':     self.free_slots,
            'time_controls':  self.time_controls,
            'remaining_time': self.remaining_time,
            'in_progress':    self.in_progress,
            'result':         self.result,
            'game_over':      self.game_over,
            'turn':           self.turn,
            'ply_count':      self.ply_count,
            'move_count':     self.move_count,
            'moves':          self.moves,
            'fen':            self.fen
        }
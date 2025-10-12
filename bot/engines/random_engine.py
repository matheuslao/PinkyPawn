import chess
import random
from .base_engine import BaseEngine

class RandomEngine(BaseEngine):
    """
    The simplest possible engine: chooses a random move.

    Serves as a baseline - any engine we build should be BETTER than this!
    """
    
    def __init__(self) -> None:
        super().__init__()

    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        """Choose a random move among all legal moves."""
        
        # board.legal_moves yields all legal moves in the position
        legal_moves = list(board.legal_moves)
        
        # Pick one at random
        return random.choice(legal_moves)

    def close(self) -> None:
        """No-op close for RandomEngine (no external resources)."""
        # Rely on BaseEngine to clear the started flag
        super().close()
        return None

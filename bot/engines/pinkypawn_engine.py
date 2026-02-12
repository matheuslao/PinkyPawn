import chess
import random

from .base_engine import BaseEngine
from typing import Dict

class PinkyPawnEngine(BaseEngine):
    """
    Empirical engine based on intuitive chess heuristics.

    Idea: evaluate each legal move by assigning points for:
    
      - Checkmate: maximum score, best possible move.
    
    """    

    def __init__(self) -> None:
        super().__init__()

    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        """Chooses the move with the best heuristic score."""
        legal_moves = list(board.legal_moves)

        # Evaluate each move
        best_score = float('-inf')
        best_moves = []

        for move in legal_moves:
            score = self._evaluate_move(board, move)

            # If checkmate found, return immediately
            if score >= 10000:
                return move

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # If there is a tie, randomly choose among the best moves
        return random.choice(best_moves)

    def _evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """Assigns a score to a move based on heuristics."""
        score = 0.0

        # 1. CHECKMATE: best possible move!
        if board.is_checkmate():
            score += 10000

     

        return score

    def close(self) -> None:
        """No external resources to clean up."""
        super().close()

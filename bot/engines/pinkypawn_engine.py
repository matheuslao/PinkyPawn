import chess
import random

from .base_engine import BaseEngine
from typing import Dict

class PinkyPawnEngine(BaseEngine):
    """
    Empirical engine based on intuitive chess heuristics.

    Idea: evaluate each legal move by assigning points for:
    
      - Checkmate: maximum score, best possible move.
      - Check: checking the opponent's king is good
      - Captures: capturing opponent's pieces is good
      - Control of the center: moves that control the center are good
    
    """

    # Heuristic values for pieces. These can be adjusted based on the engine's preferences.
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    # Central control is important in chess, so we can assign points for moves that control the center.
    CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]
    EXTENDED_CENTER = [chess.C3, chess.C4, chess.C5, chess.C6,
                       chess.D3, chess.D6,
                       chess.E3, chess.E6,
                       chess.F3, chess.F4, chess.F5, chess.F6]

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

        # 2. CHECK: checking the opponent's king is good
        if board.gives_check(move):
            score += 50

        # 3. CAPTURE: capturing opponent's pieces is good
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                score += self.PIECE_VALUES[captured_piece.piece_type] * 10

        # 4. CONTROL OF THE CENTER: moves that control the center are good
        if move.to_square in self.CENTER_SQUARES:
            score += 20
        elif move.to_square in self.EXTENDED_CENTER:
            score += 10
     

        return score

    def close(self) -> None:
        """No external resources to clean up."""
        super().close()

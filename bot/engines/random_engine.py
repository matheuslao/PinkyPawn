import chess
import random
from .base_engine import BaseEngine

class RandomEngine(BaseEngine):
    """
    Engine mais simples possível: escolhe uma jogada aleatória.
    
    Serve como baseline - qualquer engine que criarmos
    deve ser MELHOR que isso!
    """
    
    def __init__(self) -> None:
        super().__init__()

    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        """Escolhe uma jogada aleatória entre todas as possíveis"""
        
        # board.legal_moves retorna todas as jogadas legais na posição
        legal_moves = list(board.legal_moves)
        
        # Escolhe uma aleatória
        return random.choice(legal_moves)

    def close(self) -> None:
        """No-op close for RandomEngine (no external resources)."""
        # Rely on BaseEngine to clear the started flag
        super().close()
        return None

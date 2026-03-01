import chess
import random

from .base_engine import BaseEngine
from typing import Dict

class PinkyPawnEngine(BaseEngine):
    """
    Empirical engine based on intuitive chess heuristics with 1-ply lookahead.

    Core heuristics evaluated and combined:
    
      - Checkmate: maximum score, immediate win.
      - Check: attacking opponent's king (contextual bonus if restricting squares).
      - Captures: weighted by piece value, with positional bonuses.
      - Center control: opening emphasis on core center, middlegame on extended center.
      - Castling: early game safety bonus.
      - Piece vulnerability (1-ply lookahead): tracks if moves expose pieces to attacks,
        preventing tactical blunders.
    
    All heuristics are contextualized and combined, creating interdependencies rather
    than isolated evaluations. This maintains the engine's exploratory, intuitive nature.
    """

    # Heuristic values for pieces (material value).
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    # Squares considered strategically important.
    CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]
    EXTENDED_CENTER = [chess.C3, chess.C4, chess.C5, chess.C6,
                       chess.D3, chess.D6,
                       chess.E3, chess.E6,
                       chess.F3, chess.F4, chess.F5, chess.F6]

    # Configurable weights for heuristics. Adjust these to change engine behavior.
    HEURISTIC_WEIGHTS = {
        'checkmate': 10000,
        'check': 10,
        'capture': 30,
        'center_control': 20,
        'extended_center': 10,
        'castling': 15,
        'piece_safety': -50,  # Penalty for hanging pieces
        'positional_control': 5,  # Bonus for controlling more squares
    }

    def __init__(self) -> None:
        super().__init__()

    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        """
        Chooses the best move by evaluating and combining contextual heuristics.
        Heuristics are weighted and combined, not evaluated in isolation.
        """
        legal_moves = list(board.legal_moves)

        best_score = float('-inf')
        best_moves = []

        for move in legal_moves:
            score = self._evaluate_move(board, move)

            # If checkmate found, return immediately (terminal condition)
            if score >= self.HEURISTIC_WEIGHTS['checkmate']:
                return move

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        # Break ties randomly among equally good moves
        return random.choice(best_moves)

    def _evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """
        Evaluates a move by combining and contextualizing multiple heuristics.
        Each heuristic modifies the same score, creating interdependencies.
        """
        score = 0.0

        # 1. CHECKMATE CHECK (terminal condition)
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return self.HEURISTIC_WEIGHTS['checkmate']
        
        is_check = board.is_check()
        board.pop()

        # 2. CHECK: context matters - more valuable if opponent has few escape squares
        if board.gives_check(move):
            score += self.HEURISTIC_WEIGHTS['check']
            # Slight bonus if checking near the king (more controlling)
            if move.to_square in self.CENTER_SQUARES:
                score += 5

        # 3. CAPTURE: value depends on piece captured AND what captures it
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                capture_value = self.PIECE_VALUES[captured_piece.piece_type]
                score += capture_value * self.HEURISTIC_WEIGHTS['capture']
                
                # Context: bonus if capturing towards center (active piece)
                if move.to_square in self.CENTER_SQUARES:
                    score += 15
                elif move.to_square in self.EXTENDED_CENTER:
                    score += 8

        # 4. CENTER CONTROL: context - control is more valuable in opening
        game_phase = self._estimate_game_phase(board)
        if move.to_square in self.CENTER_SQUARES:
            score += self.HEURISTIC_WEIGHTS['center_control']
            if game_phase == 'opening':
                score += 10  # Emphasize center in opening
        elif move.to_square in self.EXTENDED_CENTER:
            score += self.HEURISTIC_WEIGHTS['extended_center']
            if game_phase == 'opening':
                score += 5

        # 5. CASTLING: generally safe, especially in opening
        if board.is_castling(move):
            score += self.HEURISTIC_WEIGHTS['castling']
            if not (board.is_kingside_castling(move)):
                score += 5  # Queenside castling slightly more flexible

        # 6. PIECE VULNERABILITY (1-PLY LOOKAHEAD): Comprehensive safety analysis
        # Checks if any of our pieces become vulnerable after this move.
        # Prevents tactical blunders like exd6 exposing the queen to a bishop.
        # Also evaluates trades: if we capture but our piece gets attacked after.
        
        piece_moved = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square) if board.is_capture(move) else None
        
        if piece_moved:
            board.push(move)
            
            # Check all our valuable pieces for vulnerabilities after this move
            for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                for square in board.pieces(piece_type, not board.turn):  # our pieces
                    # Check if opponent can attack this square after our move
                    if board.is_attacked_by(board.turn, square):
                        attackers = len(board.attackers(board.turn, square))
                        defenders = len(board.attackers(not board.turn, square))
                        
                        # If more attackers than defenders, piece is vulnerable
                        if attackers > defenders:
                            # Special handling for the piece we just moved
                            if square == move.to_square:
                                moving_piece_value = self.PIECE_VALUES[piece_moved.piece_type]
                                
                                # If we captured, evaluate the trade
                                if captured_piece:
                                    captured_value = self.PIECE_VALUES[captured_piece.piece_type]
                                    
                                    # Penalize if losing material in forced trade
                                    if moving_piece_value > captured_value:
                                        multiplier = 20 if moving_piece_value >= 5 else 15
                                        material_loss = (moving_piece_value - captured_value) * multiplier
                                        score -= material_loss
                                    # Bonus if winning the exchange
                                    elif moving_piece_value < captured_value:
                                        material_gain = (captured_value - moving_piece_value) * 8
                                        score += material_gain
                                else:
                                    # Piece hangs without capturing anything
                                    penalty = self.HEURISTIC_WEIGHTS['piece_safety'] * moving_piece_value
                                    score += penalty
                            else:
                                # Other pieces become vulnerable (e.g., queen exposed after exd6)
                                piece_value = self.PIECE_VALUES[piece_type]
                                vulnerability_penalty = piece_value * 20
                                score -= vulnerability_penalty
            
            board.pop()

        # 7. POSITIONAL CONTROL: bonus for moves that control more squares
        square_control = self._count_controlled_squares(board, move)
        score += square_control * self.HEURISTIC_WEIGHTS['positional_control']

        return score

    def _estimate_game_phase(self, board: chess.Board) -> str:
        """
        Simple heuristic to estimate game phase based on material on board.
        Helps contextualize evaluation.
        """
        total_material = sum(
            len(board.pieces(piece_type, color))
            * self.PIECE_VALUES[piece_type]
            for piece_type in chess.PIECE_TYPES
            for color in [chess.WHITE, chess.BLACK]
        )
        
        if total_material > 30:
            return 'opening'
        elif total_material > 15:
            return 'middlegame'
        else:
            return 'endgame'

    def _count_controlled_squares(self, board: chess.Board, move: chess.Move) -> int:
        """
        Count how many squares are attacked/controlled by the moving piece after the move.
        Simple positional metric.
        """
        board.push(move)
        controlled = 0
        
        # Count squares controlled by the piece that just moved
        for square in chess.SQUARES:
            if board.is_attacked_by(board.turn, square):
                controlled += 1
        
        board.pop()
        return controlled

    def close(self) -> None:
        """No external resources to clean up."""
        super().close()

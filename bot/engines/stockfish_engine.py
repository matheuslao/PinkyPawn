import chess
import chess.engine
from .base_engine import BaseEngine
from typing import Optional


class StockfishEngine(BaseEngine):
    """Adapter around python-chess' SimpleEngine for Stockfish.

    This implementation defers launching the external process to ``start()``
    so the engine lifecycle is consistent with ``BaseEngine``'s context
    manager semantics.
    """

    def __init__(self, path: str, skill_level: int = 10, threads: int = 1):
        super().__init__()
        self.path = path
        self.skill_level = skill_level
        self.threads = threads
        self._engine: Optional[chess.engine.SimpleEngine] = None

    def start(self) -> None:
        """Start the Stockfish process. Overrides BaseEngine.start."""
        # Call base to set the started flag
        super().start()
        # Launch engine process
        self._engine = chess.engine.SimpleEngine.popen_uci(self.path)
        # Configure engine parameters if supported
        try:
            self._engine.configure({
                "Skill Level": self.skill_level,
                "Threads": self.threads,
            })
        except Exception:
            # Some builds may not support configure; ignore silently
            pass

    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        # Ensure the engine process is running. Start lazily for backward
        # compatibility (previous implementation launched engine in __init__).
        if self._engine is None:
            try:
                self.start()
            except Exception as e:
                raise RuntimeError(f"Engine failed to start: {e}") from e

        if self._engine is None:
            raise RuntimeError("Engine not started")

        result = self._engine.play(board, chess.engine.Limit(time=time_limit))
        move = result.move
        if move is None:
            raise RuntimeError("Engine returned no move")
        return move

    def close(self) -> None:
        # Try to quit external engine if present, then call base close
        if self._engine is not None:
            try:
                self._engine.quit()
            finally:
                self._engine = None
        super().close()

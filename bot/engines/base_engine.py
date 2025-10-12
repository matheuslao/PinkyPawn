from abc import ABC, abstractmethod
import chess
from typing import Any


class BaseEngine(ABC):
    """Base class that all engines should inherit from.

    This acts as a contract for our program: engines must implement
    ``get_move`` and may override lifecycle hooks such as ``start`` and
    ``close``. The base class also provides a convenient context-manager
    interface so engines can be used with ``with`` and ensures resources
    are cleaned up on exit.
    """

    def __init__(self) -> None:
        # Use getattr in helpers so subclasses that don't call super().__init__()
        # will still be compatible.
        self._started: bool = False

    # --- contract -----------------------------------------------------
    @abstractmethod
    def get_move(self, board: chess.Board, time_limit: float) -> chess.Move:
        """Return a legal move for the given ``board`` within ``time_limit`` seconds.

        Args:
            board: current chess.Board position
            time_limit: thinking time in seconds

        Returns:
            A legal ``chess.Move`` for the position.
        """

    # --- lifecycle / helpers -----------------------------------------
    def start(self) -> None:
        """Optional hook to start engine resources (processes, threads...).

        Default implementation simply marks the engine as started. Engines
        that need to launch external processes may override this method.
        """
        self._started = True

    def close(self) -> None:
        """Close or release any resources held by the engine.

        Default implementation is a no-op that marks the engine as stopped.
        Subclasses that manage external resources (processes, sockets) MUST
        override this to perform proper cleanup.
        """
        self._started = False

    @property
    def started(self) -> bool:
        """Whether the engine has been started (best-effort)."""
        return getattr(self, "_started", False)

    @property
    def name(self) -> str:
        """Human-readable engine name (defaults to class name)."""
        return self.__class__.__name__

    # Context-manager support: ensures ``close`` is always called.
    def __enter__(self) -> "BaseEngine":
        try:
            self.start()
        except Exception:
            # If start fails, ensure we don't leave an inconsistent state.
            self._started = False
            raise
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        # Always try to close resources. Do not suppress exceptions.
        try:
            self.close()
        finally:
            # Ensure internal flag is cleared even if subclass close fails.
            self._started = False


import berserk
import chess
import chess.engine
import threading
import logging
from config import Config
from engines.base_engine import BaseEngine
from engines.random_engine import RandomEngine
from engines.stockfish_engine import StockfishEngine
from engines.pinkypawn_engine import PinkyPawnEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LichessBot:
    def __init__(self):
        Config.validate()
        
        session = berserk.TokenSession(Config.LICHESS_TOKEN)
        self.client = berserk.Client(session)

    # Instantiate the configured engine
        impl = Config.ENGINE_IMPLEMENTATION.lower()
        if impl == 'stockfish':
            self.engine: BaseEngine = StockfishEngine(
                path=Config.STOCKFISH_PATH,
                skill_level=Config.ENGINE_SKILL_LEVEL,
                threads=Config.ENGINE_THREADS,
            )
        elif impl == 'random':
            self.engine = RandomEngine()
        elif impl == 'pinkypawn':
            self.engine = PinkyPawnEngine()
        else:
            raise ValueError(f"Unknown engine implementation: {Config.ENGINE_IMPL}")
        
        logger.info("Bot initialized successfully!")
        logger.info(f"Engine implementation: {impl}")
        logger.info(f"Engine Skill Level: {Config.ENGINE_SKILL_LEVEL}")
        
    def should_accept_challenge(self, challenge):
        """Check whether a challenge should be accepted."""
        variant = challenge['variant']['key']
        rated = challenge['rated']
        
        # Check variant
        if variant not in Config.ACCEPT_VARIANTS:
            logger.info(f"Challenge rejected: variant {variant} not accepted")
            return False
        
        # Check rated/casual preference
        if rated and not Config.ACCEPT_RATED:
            logger.info("Challenge rejected: rated games not accepted")
            return False
        
        if not rated and not Config.ACCEPT_CASUAL:
            logger.info("Challenge rejected: casual games not accepted")
            return False
        
    # Check opponent rating (if available)
        challenger = challenge.get('challenger', {})
        rating = challenger.get('rating')
        
        if rating:
            if rating < Config.MIN_RATING or rating > Config.MAX_RATING:
                logger.info(f"Challenge rejected: rating {rating} out of range")
                return False
        
        return True
        
    def accept_challenge(self, event):
        """Accept or decline challenges."""
        if event['type'] == 'challenge':
            challenge = event['challenge']
            challenge_id = challenge['id']
            challenger_name = challenge['challenger']['name']
            
            logger.info(f"Challenge received from {challenger_name}")
            
            if self.should_accept_challenge(challenge):
                try:
                    self.client.challenges.accept(challenge_id)
                    logger.info(f"Challenge {challenge_id} accepted!")
                except Exception as e:
                    logger.error(f"Error accepting challenge: {e}")
            else:
                try:
                    self.client.challenges.decline(challenge_id)
                    logger.info(f"Challenge {challenge_id} declined")
                except Exception as e:
                    logger.error(f"Error declining challenge: {e}")
    
    def play_game(self, game_id):
        """Play a game using the bot API."""
        board = chess.Board()
        logger.info(f"Game started: {game_id}")
        
        try:
            for event in self.client.bots.stream_game_state(game_id):
                if event['type'] == 'gameFull':
                    # Process initial state if present
                    if event.get('state'):
                        self.handle_state(game_id, board, event['state'])
                        
                elif event['type'] == 'gameState':
                    self.handle_state(game_id, board, event)
                    
                elif event['type'] == 'chatLine':
                    # Optional: log chat messages
                    username = event.get('username', 'Unknown')
                    text = event.get('text', '')
                    logger.info(f"Chat [{username}]: {text}")
                    
        except Exception as e:
            logger.error(f"Error in game {game_id}: {e}")
        
        logger.info(f"Game finished: {game_id}")
    
    def handle_state(self, game_id, board, state):
        """Process the game state and make a move."""
        moves = state.get('moves', '')
        
        if not moves:
            # Start of the game, no moves yet
            move_list = []
        else:
            move_list = moves.split()
        
        # Rebuild the board from all moves
        board = chess.Board()
        for move in move_list:
            try:
                board.push_uci(move)
            except Exception as e:
                logger.error(f"Error processing move {move}: {e}")
                return
        
        # Check if it's our turn
        status = state.get('status', '')
        if board.is_game_over():
            logger.info(f"Game {game_id} ended: {board.result()}")
            return
            
        if status != 'started':
            logger.info(f"Game {game_id} status: {status}")
            return
        
        # Check whose turn it is
        # If the number of moves is even we are white, if odd we are black
        # We need to check our color
        logger.info(f"Current position: {len(move_list)} moves, turn: {'white' if board.turn else 'black'}")
        
        # Calculate the best move
        logger.info(f"Calculating move for {game_id}...")
        
        try:
            # Use our engine layer to obtain the move
            move = self.engine.get_move(board, Config.ENGINE_TIME_LIMIT)

            if move is None:
                logger.error(f"Engine returned move None!")
                return

            # Send the move using bots API
            self.client.bots.make_move(game_id, move.uci())

            # Log the move in a more readable format
            san_move = board.san(move)
            logger.info(f"Move sent: {move.uci()} ({san_move})")
            
        except Exception as e:
            logger.error(f"Error calculating/sending move: {e}")
    
    def start(self):
        """Start the bot."""
        logger.info("Bot waiting for challenges...")
        
        try:
            for event in self.client.bots.stream_incoming_events():
                if event['type'] == 'challenge':
                    self.accept_challenge(event)
                    
                elif event['type'] == 'gameStart':
                    game_id = event['game']['id']
                    logger.info(f"New game detected: {game_id}")
                    game_thread = threading.Thread(
                        target=self.play_game, 
                        args=(game_id,),
                        daemon=True
                    )
                    game_thread.start()
                    
                elif event['type'] == 'gameFinish':
                    game_id = event['game']['id']
                    logger.info(f"Game finished: {game_id}")
                    
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the bot."""
        logger.info("Shutting down bot...")
        try:
            # Close abstract engine
            try:
                self.engine.close()
            except Exception as e:
                logger.error(f"Error closing engine: {e}")
        except Exception as e:
            logger.error(f"Error closing engine: {e}")
        logger.info("Bot shut down!")

if __name__ == "__main__":
    # Create logs directory if it does not exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    bot = LichessBot()
    bot.start()

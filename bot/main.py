import berserk
import chess
import chess.engine
import threading
import logging
from config import Config
from engines.base_engine import BaseEngine
from engines.random_engine import RandomEngine
from engines.stockfish_engine import StockfishEngine

# Configura logging
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

        # Instancia a engine configurada
        impl = Config.ENGINE_IMPLEMENTATION.lower()
        if impl == 'stockfish':
            self.engine: BaseEngine = StockfishEngine(
                path=Config.STOCKFISH_PATH,
                skill_level=Config.ENGINE_SKILL_LEVEL,
                threads=Config.ENGINE_THREADS,
            )
        elif impl == 'random':
            self.engine = RandomEngine()
        else:
            raise ValueError(f"Engine implementation desconhecida: {Config.ENGINE_IMPL}")
        
        logger.info("Bot inicializado com sucesso!")
        logger.info(f"Engine implementation: {impl}")
        logger.info(f"Engine Skill Level: {Config.ENGINE_SKILL_LEVEL}")
        
    def should_accept_challenge(self, challenge):
        """Verifica se deve aceitar um desafio"""
        variant = challenge['variant']['key']
        rated = challenge['rated']
        
        # Verifica variante
        if variant not in Config.ACCEPT_VARIANTS:
            logger.info(f"Desafio rejeitado: variante {variant} não aceita")
            return False
        
        # Verifica se é rated/casual
        if rated and not Config.ACCEPT_RATED:
            logger.info("Desafio rejeitado: partidas rated não aceitas")
            return False
        
        if not rated and not Config.ACCEPT_CASUAL:
            logger.info("Desafio rejeitado: partidas casual não aceitas")
            return False
        
        # Verifica rating do oponente (se disponível)
        challenger = challenge.get('challenger', {})
        rating = challenger.get('rating')
        
        if rating:
            if rating < Config.MIN_RATING or rating > Config.MAX_RATING:
                logger.info(f"Desafio rejeitado: rating {rating} fora do intervalo")
                return False
        
        return True
        
    def accept_challenge(self, event):
        """Aceita ou rejeita desafios"""
        if event['type'] == 'challenge':
            challenge = event['challenge']
            challenge_id = challenge['id']
            challenger_name = challenge['challenger']['name']
            
            logger.info(f"Desafio recebido de {challenger_name}")
            
            if self.should_accept_challenge(challenge):
                try:
                    self.client.challenges.accept(challenge_id)
                    logger.info(f"Desafio {challenge_id} aceito!")
                except Exception as e:
                    logger.error(f"Erro ao aceitar desafio: {e}")
            else:
                try:
                    self.client.challenges.decline(challenge_id)
                    logger.info(f"Desafio {challenge_id} rejeitado")
                except Exception as e:
                    logger.error(f"Erro ao rejeitar desafio: {e}")
    
    def play_game(self, game_id):
        """Joga uma partida usando bot API"""
        board = chess.Board()
        logger.info(f"Jogo iniciado: {game_id}")
        
        try:
            for event in self.client.bots.stream_game_state(game_id):
                if event['type'] == 'gameFull':
                    # Processa estado inicial se existir
                    if event.get('state'):
                        self.handle_state(game_id, board, event['state'])
                        
                elif event['type'] == 'gameState':
                    self.handle_state(game_id, board, event)
                    
                elif event['type'] == 'chatLine':
                    # Opcional: log de mensagens do chat
                    username = event.get('username', 'Unknown')
                    text = event.get('text', '')
                    logger.info(f"Chat [{username}]: {text}")
                    
        except Exception as e:
            logger.error(f"Erro no jogo {game_id}: {e}")
        
        logger.info(f"Jogo finalizado: {game_id}")
    
    def handle_state(self, game_id, board, state):
        """Processa o estado do jogo e faz a jogada"""
        moves = state.get('moves', '')
        
        if not moves:
            # Início do jogo, sem jogadas ainda
            move_list = []
        else:
            move_list = moves.split()
        
        # Reconstrói o tabuleiro com todas as jogadas
        board = chess.Board()
        for move in move_list:
            try:
                board.push_uci(move)
            except Exception as e:
                logger.error(f"Erro ao processar jogada {move}: {e}")
                return
        
        # Verifica se é nossa vez
        status = state.get('status', '')
        if board.is_game_over():
            logger.info(f"Jogo {game_id} finalizado: {board.result()}")
            return
            
        if status != 'started':
            logger.info(f"Jogo {game_id} com status: {status}")
            return
        
        # Verifica de quem é a vez
        # Se o número de jogadas for par e somos brancas, ou ímpar e somos pretas
        # Precisamos verificar nossa cor
        logger.info(f"Posição atual: {len(move_list)} jogadas, vez: {'brancas' if board.turn else 'pretas'}")
        
        # Calcula a melhor jogada
        logger.info(f"Calculando jogada para {game_id}...")
        
        try:
            # Use nossa camada de engine para obter a jogada
            move = self.engine.get_move(board, Config.ENGINE_TIME_LIMIT)

            if move is None:
                logger.error(f"Engine retornou jogada None!")
                return

            # Envia a jogada usando bots API
            self.client.bots.make_move(game_id, move.uci())

            # Log da jogada em formato mais legível
            san_move = board.san(move)
            logger.info(f"Jogada enviada: {move.uci()} ({san_move})")
            
        except Exception as e:
            logger.error(f"Erro ao calcular/enviar jogada: {e}")
    
    def start(self):
        """Inicia o bot"""
        logger.info("Bot aguardando desafios...")
        
        try:
            for event in self.client.bots.stream_incoming_events():
                if event['type'] == 'challenge':
                    self.accept_challenge(event)
                    
                elif event['type'] == 'gameStart':
                    game_id = event['game']['id']
                    logger.info(f"Novo jogo detectado: {game_id}")
                    game_thread = threading.Thread(
                        target=self.play_game, 
                        args=(game_id,),
                        daemon=True
                    )
                    game_thread.start()
                    
                elif event['type'] == 'gameFinish':
                    game_id = event['game']['id']
                    logger.info(f"Jogo finalizado: {game_id}")
                    
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro fatal: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Finaliza o bot"""
        logger.info("Encerrando bot...")
        try:
            # Fecha engine abstrata
            try:
                self.engine.close()
            except Exception as e:
                logger.error(f"Erro ao fechar engine: {e}")
        except Exception as e:
            logger.error(f"Erro ao fechar engine: {e}")
        logger.info("Bot finalizado!")

if __name__ == "__main__":
    # Cria diretório de logs se não existir
    import os
    os.makedirs('logs', exist_ok=True)
    
    bot = LichessBot()
    bot.start()

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Config:
    # Lichess
    LICHESS_TOKEN = os.getenv('LICHESS_TOKEN')

    # Engine implementation: 'stockfish' or 'random'
    ENGINE_IMPLEMENTATION = os.getenv('ENGINE_IMPLEMENTATION', 'stockfish')
    
    # Stockfish
    STOCKFISH_PATH = os.getenv('STOCKFISH_PATH', '/usr/local/bin/stockfish')
    ENGINE_SKILL_LEVEL = int(os.getenv('ENGINE_SKILL_LEVEL', 10))
    ENGINE_THREADS = int(os.getenv('ENGINE_THREADS', 2))
    ENGINE_TIME_LIMIT = float(os.getenv('ENGINE_TIME_LIMIT', 2.0))
    
    
    # Filtros
    ACCEPT_VARIANTS = os.getenv('ACCEPT_VARIANTS', 'standard').split(',')
    MIN_RATING = int(os.getenv('MIN_RATING', 0))
    MAX_RATING = int(os.getenv('MAX_RATING', 3000))
    ACCEPT_CASUAL = os.getenv('ACCEPT_CASUAL', 'true').lower() == 'true'
    ACCEPT_RATED = os.getenv('ACCEPT_RATED', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Valida configurações obrigatórias"""
        if not cls.LICHESS_TOKEN:
            raise ValueError("LICHESS_TOKEN não configurado!")
        return True

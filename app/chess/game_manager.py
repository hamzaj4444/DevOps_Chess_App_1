"""Game session management for chess games."""

import uuid
from typing import Dict, Optional
import chess
from datetime import datetime
from app.logger import logger

class GameSession:
    """Represents a single chess game session."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.board = chess.Board()
        self.created_at = datetime.utcnow()
        self.moves = []
        self.is_active = True
        
    def get_fen(self) -> str:
        """Get current board position in FEN notation."""
        return self.board.fen()
    
    def make_move(self, move_uci: str) -> bool:
        """
        Make a move on the board.
        
        Args:
            move_uci: Move in UCI notation (e.g., 'e2e4')
            
        Returns:
            bool: True if move was successful
            
        Raises:
            ValueError: If move is invalid
        """
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in self.board.legal_moves:
                raise ValueError(f"Illegal move: {move_uci}")
            
            self.board.push(move)
            self.moves.append(move_uci)
            logger.info(f"Move made in game {self.game_id}: {move_uci}")
            
            # Check if game is over
            if self.board.is_game_over():
                self.is_active = False
                logger.info(f"Game {self.game_id} ended. Result: {self.get_result()}")
            
            return True
        except Exception as e:
            logger.error(f"Invalid move {move_uci} in game {self.game_id}: {e}")
            raise ValueError(f"Invalid move: {e}")
    
    def get_result(self) -> Optional[str]:
        """Get game result if game is over."""
        if not self.board.is_game_over():
            return None
        
        if self.board.is_checkmate():
            winner = "black" if self.board.turn == chess.WHITE else "white"
            return f"{winner}_wins"
        elif self.board.is_stalemate():
            return "stalemate"
        elif self.board.is_insufficient_material():
            return "insufficient_material"
        elif self.board.can_claim_draw():
            return "draw"
        else:
            return "draw"
    
    def to_dict(self) -> dict:
        """Convert game session to dictionary."""
        return {
            "game_id": self.game_id,
            "fen": self.get_fen(),
            "moves": self.moves,
            "is_active": self.is_active,
            "is_check": self.board.is_check(),
            "is_game_over": self.board.is_game_over(),
            "result": self.get_result(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "created_at": self.created_at.isoformat()
        }


class GameManager:
    """Manages all active chess game sessions."""
    
    def __init__(self):
        self.games: Dict[str, GameSession] = {}
        logger.info("Chess GameManager initialized")
    
    def create_game(self) -> GameSession:
        """Create a new game session."""
        game_id = str(uuid.uuid4())
        game = GameSession(game_id)
        self.games[game_id] = game
        logger.info(f"New chess game created: {game_id}")
        return game
    
    def get_game(self, game_id: str) -> Optional[GameSession]:
        """Get a game session by ID."""
        return self.games.get(game_id)
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game session."""
        if game_id in self.games:
            del self.games[game_id]
            logger.info(f"Game {game_id} deleted")
            return True
        return False
    
    def get_active_games_count(self) -> int:
        """Get count of active games."""
        return sum(1 for game in self.games.values() if game.is_active)
    
    def cleanup_old_games(self, max_age_hours: int = 24):
        """Remove games older than specified hours."""
        now = datetime.utcnow()
        to_delete = []
        
        for game_id, game in self.games.items():
            age = (now - game.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_delete.append(game_id)
        
        for game_id in to_delete:
            self.delete_game(game_id)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old games")


# Global game manager instance
game_manager = GameManager()

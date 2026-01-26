"""Chess game API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time

from app.chess.bot import get_bot_move
from app.chess.game_manager import game_manager
from app.logger import logger
from app.metrics import (
    CHESS_GAMES_TOTAL,
    CHESS_MOVES_TOTAL,
    CHESS_BOT_MOVE_DURATION,
    CHESS_GAMES_ACTIVE,
    CHESS_GAME_OUTCOMES
)

router = APIRouter(prefix="/chess", tags=["chess"])


# Request/Response models
class FenRequest(BaseModel):
    fen: str = Field(..., description="Board position in FEN notation")


class MoveResponse(BaseModel):
    move: str = Field(..., description="Move in UCI notation (e.g., 'e2e4')")


class GameResponse(BaseModel):
    game_id: str
    fen: str
    moves: list
    is_active: bool
    is_check: bool
    is_game_over: bool
    result: Optional[str]
    turn: str
    created_at: str


class MakeMoveRequest(BaseModel):
    move: str = Field(..., description="Move in UCI notation")


@router.get("/health")
def chess_health():
    """Health check for chess module."""
    return {
        "status": "ok",
        "module": "chess",
        "active_games": game_manager.get_active_games_count()
    }


@router.post("/move", response_model=MoveResponse)
def get_move(req: FenRequest):
    """
    Get bot move for a given board position.
    
    This is a stateless endpoint - just give it a FEN and get a move back.
    """
    try:
        start_time = time.time()
        move = get_bot_move(req.fen, log_analysis=False)
        duration = time.time() - start_time
        
        CHESS_BOT_MOVE_DURATION.observe(duration)
        
        logger.info(f"Bot move calculated in {duration:.3f}s")
        return {"move": move}
    
    except ValueError as e:
        logger.warning(f"Invalid FEN or game over: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating bot move: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate move")


@router.post("/game/new", response_model=GameResponse)
def create_game():
    """Create a new chess game session."""
    try:
        game = game_manager.create_game()
        
        CHESS_GAMES_TOTAL.inc()
        CHESS_GAMES_ACTIVE.set(game_manager.get_active_games_count())
        
        logger.info(f"New game created: {game.game_id}")
        return game.to_dict()
    
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(status_code=500, detail="Failed to create game")


@router.get("/game/{game_id}", response_model=GameResponse)
def get_game(game_id: str):
    """Get game state by ID."""
    game = game_manager.get_game(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game.to_dict()


@router.post("/game/{game_id}/move", response_model=GameResponse)
def make_move(game_id: str, req: MakeMoveRequest):
    """
    Make a move in a game session.
    
    After the player's move, the bot will automatically respond with its move.
    """
    game = game_manager.get_game(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game.is_active:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    try:
        # Make player's move
        game.make_move(req.move)
        
        CHESS_MOVES_TOTAL.labels(color="player").inc()
        
        # If game is over after player's move, return
        if game.is_active and not game.board.is_game_over():
            # Get bot's response move
            start_time = time.time()
            bot_move = get_bot_move(game.get_fen(), log_analysis=False)
            duration = time.time() - start_time
            
            CHESS_BOT_MOVE_DURATION.observe(duration)
            
            game.make_move(bot_move)
            
            CHESS_MOVES_TOTAL.labels(color="bot").inc()
            
            logger.info(f"Bot responded with {bot_move} in {duration:.3f}s")
        
        # Update metrics if game ended
        if not game.is_active:
            result = game.get_result()
            if result:
                CHESS_GAME_OUTCOMES.labels(result=result).inc()
        
        CHESS_GAMES_ACTIVE.set(game_manager.get_active_games_count())
        
        return game.to_dict()
    
    except ValueError as e:
        logger.warning(f"Invalid move in game {game_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error making move in game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to make move")


@router.delete("/game/{game_id}")
def delete_game(game_id: str):
    """Delete a game session."""
    success = game_manager.delete_game(game_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Game not found")
    
    CHESS_GAMES_ACTIVE.set(game_manager.get_active_games_count())
    
    return {"message": "Game deleted successfully"}

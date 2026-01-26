import torch
import chess
import numpy as np
import os
from pathlib import Path
from app.chess.model import ChessNet
from app.logger import logger

# Model path - relative to app directory
MODEL_PATH = Path(__file__).parent / "model.pth"

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ChessNet().to(device)

try:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    logger.info(f"Chess model loaded successfully from {MODEL_PATH}")
except FileNotFoundError as e:
    logger.error(f"Model file not found: {e}")
    raise
except Exception as e:
    logger.error(f"Error loading chess model: {e}")
    raise

model.eval()

def board_to_tensor(board):
    """Convert chess board to neural network input tensor."""
    pieces = [
        chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING
    ]
    tensor = np.zeros((8, 8, 12), dtype=np.float32)
    
    for i, piece_type in enumerate(pieces):
        for sq in board.pieces(piece_type, chess.WHITE):
            row, col = divmod(sq, 8)
            tensor[7-row, col, i] = 1.0
        for sq in board.pieces(piece_type, chess.BLACK):
            row, col = divmod(sq, 8)
            tensor[7-row, col, i + 6] = 1.0
            
    return torch.from_numpy(tensor).unsqueeze(0)

def evaluate_board(board):
    """Simple material evaluation for tactical search."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    score = 0
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax search with alpha-beta pruning for tactical evaluation."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing_player:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_bot_move(fen, log_analysis=False):
    """
    Get the best move for the given board position.
    
    Args:
        fen: Board position in FEN notation
        log_analysis: Whether to log move analysis (default False for production)
    
    Returns:
        str: Move in UCI notation (e.g., 'e2e4')
    
    Raises:
        ValueError: If FEN is invalid or game is over
    """
    try:
        board = chess.Board(fen)
    except Exception as e:
        logger.error(f"Invalid FEN string: {fen}, error: {e}")
        raise ValueError(f"Invalid FEN string: {e}")
    
    if board.is_game_over():
        logger.warning(f"Game is over for FEN: {fen}")
        raise ValueError("Game is already over")
    
    # Get Neural Network style scores
    tensor = board_to_tensor(board).to(device)
    with torch.no_grad():
        output = model(tensor)
    probs = torch.softmax(output, dim=1)[0]
    
    # Search to depth 2 for tactical safety
    best_move = None
    legal_moves = list(board.legal_moves)
    scored_moves = []

    for move in legal_moves:
        # 1. Get Style Score (from Neural Network)
        idx = move.from_square * 64 + move.to_square
        style_score = probs[idx].item()
        
        # 2. Get Tactical Score (from Search)
        board.push(move)
        tactical_eval = minimax(board, 2, -float('inf'), float('inf'), board.turn == chess.WHITE)
        board.pop()
        
        # Combine: Tactical eval is most important, style score breaks ties
        combined_score = tactical_eval + (style_score * 50 if board.turn == chess.WHITE else -style_score * 50)
        
        scored_moves.append((move, combined_score, style_score))

    # Sort based on turn
    if board.turn == chess.WHITE:
        scored_moves.sort(key=lambda x: x[1], reverse=True)
    else:
        scored_moves.sort(key=lambda x: x[1], reverse=False)

    best_move = scored_moves[0][0]
    
    if log_analysis:
        logger.info(f"Bot analysis for {fen}:")
        for i, (move, combined, style) in enumerate(scored_moves[:5]):
            logger.info(f"  {i+1}. {move.uci()}: style={style*100:.1f}%, tactical={combined:.0f}")
    
    logger.info(f"Bot chose move: {best_move.uci()} for turn: {'white' if board.turn == chess.WHITE else 'black'}")
    
    return best_move.uci()

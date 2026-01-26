import pytest
from fastapi.testclient import TestClient
import chess
from app.main import app
from app.chess.game_manager import game_manager

client = TestClient(app)

def test_chess_health():
    """Test the chess health endpoint."""
    response = client.get("/chess/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["module"] == "chess"
    assert "active_games" in data

def test_chess_move_stateless():
    """Test the stateless bot move endpoint."""
    # Starting position
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    response = client.post("/chess/move", json={"fen": fen})
    assert response.status_code == 200
    data = response.json()
    assert "move" in data
    assert isinstance(data["move"], str)
    # Check if it's a valid UCI move
    assert chess.Move.from_uci(data["move"])

def test_invalid_fen():
    """Test that invalid FEN returns 400."""
    response = client.post("/chess/move", json={"fen": "invalid-fen-string"})
    assert response.status_code == 400

def test_game_lifecycle():
    """Test creating, playing, and deleting a game."""
    # 1. Create a new game
    response = client.post("/chess/game/new")
    assert response.status_code == 200
    game_data = response.json()
    game_id = game_data["game_id"]
    assert game_id
    assert game_data["is_active"] is True
    assert game_data["turn"] == "white"

    # 2. Get game state
    response = client.get(f"/chess/game/{game_id}")
    assert response.status_code == 200
    assert response.json()["game_id"] == game_id

    # 3. Make a move (e2e4)
    # The bot should automatically respond, so the board will have 2 moves total
    response = client.post(f"/chess/game/{game_id}/move", json={"move": "e2e4"})
    assert response.status_code == 200
    updated_game = response.json()
    assert len(updated_game["moves"]) == 2
    assert updated_game["moves"][0] == "e2e4"
    assert updated_game["turn"] == "white"  # Black (bot) moved, so it's White's turn again

    # 4. Try illegal move
    response = client.post(f"/chess/game/{game_id}/move", json={"move": "e2e5"})
    assert response.status_code == 400

    # 5. Delete game
    response = client.delete(f"/chess/game/{game_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Game deleted successfully"

    # 6. Verify deleted
    response = client.get(f"/chess/game/{game_id}")
    assert response.status_code == 404

def test_game_manager_cleanup():
    """Test game manager logic independently."""
    # This just ensures we can access the manager and it behaves
    initial_count = game_manager.get_active_games_count()
    game = game_manager.create_game()
    assert game_manager.get_active_games_count() == initial_count + 1
    game_manager.delete_game(game.game_id)
    assert game_manager.get_active_games_count() == initial_count

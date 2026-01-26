"""Chess game module for the DevOps Chess App.

This module provides a chess bot that plays using a neural network trained
on user games. It includes API endpoints for playing against the bot.
"""

from app.chess.bot import get_bot_move

__all__ = ["get_bot_move"]

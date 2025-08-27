from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import random
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Enums
class PieceType(str, Enum):
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"

class PieceColor(str, Enum):
    WHITE = "white"
    BLACK = "black"

class GameMode(str, Enum):
    PVP = "pvp"
    PVB = "pvb"  # Player vs Bot

class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

# Models
class Piece(BaseModel):
    type: PieceType
    color: PieceColor
    position: str  # e.g., "e4"
    has_moved: bool = False

class Move(BaseModel):
    from_pos: str
    to_pos: str
    piece_type: PieceType
    captured_piece: Optional[PieceType] = None
    is_castling: bool = False
    is_en_passant: bool = False
    promotion_piece: Optional[PieceType] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: GameMode
    white_player: str
    black_player: str
    current_turn: PieceColor = PieceColor.WHITE
    board_state: Dict[str, Dict[str, Any]]  # position -> piece data
    moves_history: List[Move] = []
    game_status: GameStatus = GameStatus.IN_PROGRESS
    winner: Optional[PieceColor] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    last_move_at: datetime = Field(default_factory=lambda: datetime.now())

class GameCreate(BaseModel):
    mode: GameMode
    white_player: str
    black_player: str

class MoveRequest(BaseModel):
    game_id: str
    from_pos: str
    to_pos: str
    promotion_piece: Optional[PieceType] = None

class Bot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    difficulty: int  # 1-10
    description: str


# Chess Engine
class ChessEngine:
    @staticmethod
    def create_initial_board():
        """Create the initial chess board setup"""
        board = {}
        
        # White pieces
        board["a1"] = {"type": "rook", "color": "white", "has_moved": False}
        board["b1"] = {"type": "knight", "color": "white", "has_moved": False}
        board["c1"] = {"type": "bishop", "color": "white", "has_moved": False}
        board["d1"] = {"type": "queen", "color": "white", "has_moved": False}
        board["e1"] = {"type": "king", "color": "white", "has_moved": False}
        board["f1"] = {"type": "bishop", "color": "white", "has_moved": False}
        board["g1"] = {"type": "knight", "color": "white", "has_moved": False}
        board["h1"] = {"type": "rook", "color": "white", "has_moved": False}
        
        for file in "abcdefgh":
            board[f"{file}2"] = {"type": "pawn", "color": "white", "has_moved": False}
        
        # Black pieces
        board["a8"] = {"type": "rook", "color": "black", "has_moved": False}
        board["b8"] = {"type": "knight", "color": "black", "has_moved": False}
        board["c8"] = {"type": "bishop", "color": "black", "has_moved": False}
        board["d8"] = {"type": "queen", "color": "black", "has_moved": False}
        board["e8"] = {"type": "king", "color": "black", "has_moved": False}
        board["f8"] = {"type": "bishop", "color": "black", "has_moved": False}
        board["g8"] = {"type": "knight", "color": "black", "has_moved": False}
        board["h8"] = {"type": "rook", "color": "black", "has_moved": False}
        
        for file in "abcdefgh":
            board[f"{file}7"] = {"type": "pawn", "color": "black", "has_moved": False}
        
        return board

    @staticmethod
    def pos_to_coords(pos):
        """Convert chess position to coordinates"""
        file = ord(pos[0]) - ord('a')
        rank = int(pos[1]) - 1
        return file, rank

    @staticmethod
    def coords_to_pos(file, rank):
        """Convert coordinates to chess position"""
        if 0 <= file < 8 and 0 <= rank < 8:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    @staticmethod
    def is_valid_move(board, from_pos, to_pos, player_color):
        """Validate if a move is legal"""
        if from_pos not in board:
            return False
        
        piece = board[from_pos]
        if piece["color"] != player_color:
            return False
        
        # Check if destination has own piece
        if to_pos in board and board[to_pos]["color"] == player_color:
            return False
        
        piece_type = piece["type"]
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        if piece_type == "pawn":
            return ChessEngine._is_valid_pawn_move(board, from_pos, to_pos, player_color)
        elif piece_type == "rook":
            return ChessEngine._is_valid_rook_move(board, from_pos, to_pos)
        elif piece_type == "knight":
            return ChessEngine._is_valid_knight_move(from_pos, to_pos)
        elif piece_type == "bishop":
            return ChessEngine._is_valid_bishop_move(board, from_pos, to_pos)
        elif piece_type == "queen":
            return ChessEngine._is_valid_queen_move(board, from_pos, to_pos)
        elif piece_type == "king":
            return ChessEngine._is_valid_king_move(board, from_pos, to_pos)
        
        return False

    @staticmethod
    def _is_valid_pawn_move(board, from_pos, to_pos, color):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        direction = 1 if color == "white" else -1
        start_rank = 1 if color == "white" else 6
        
        # Forward move
        if from_file == to_file:
            if to_pos not in board:  # Empty square
                if to_rank == from_rank + direction:  # One square forward
                    return True
                elif from_rank == start_rank and to_rank == from_rank + 2 * direction:  # Two squares from start
                    return True
        
        # Diagonal capture
        elif abs(from_file - to_file) == 1 and to_rank == from_rank + direction:
            if to_pos in board and board[to_pos]["color"] != color:
                return True
        
        return False

    @staticmethod
    def _is_valid_rook_move(board, from_pos, to_pos):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        if from_file != to_file and from_rank != to_rank:
            return False
        
        return ChessEngine._is_path_clear(board, from_pos, to_pos)

    @staticmethod
    def _is_valid_knight_move(from_pos, to_pos):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        file_diff = abs(from_file - to_file)
        rank_diff = abs(from_rank - to_rank)
        
        return (file_diff == 2 and rank_diff == 1) or (file_diff == 1 and rank_diff == 2)

    @staticmethod
    def _is_valid_bishop_move(board, from_pos, to_pos):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        if abs(from_file - to_file) != abs(from_rank - to_rank):
            return False
        
        return ChessEngine._is_path_clear(board, from_pos, to_pos)

    @staticmethod
    def _is_valid_queen_move(board, from_pos, to_pos):
        return (ChessEngine._is_valid_rook_move(board, from_pos, to_pos) or 
                ChessEngine._is_valid_bishop_move(board, from_pos, to_pos))

    @staticmethod
    def _is_valid_king_move(board, from_pos, to_pos):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        file_diff = abs(from_file - to_file)
        rank_diff = abs(from_rank - to_rank)
        
        return file_diff <= 1 and rank_diff <= 1 and (file_diff + rank_diff > 0)

    @staticmethod
    def _is_path_clear(board, from_pos, to_pos):
        from_file, from_rank = ChessEngine.pos_to_coords(from_pos)
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        
        file_step = 0 if from_file == to_file else (1 if to_file > from_file else -1)
        rank_step = 0 if from_rank == to_rank else (1 if to_rank > from_rank else -1)
        
        current_file = from_file + file_step
        current_rank = from_rank + rank_step
        
        while (current_file, current_rank) != (to_file, to_rank):
            pos = ChessEngine.coords_to_pos(current_file, current_rank)
            if pos in board:
                return False
            current_file += file_step
            current_rank += rank_step
        
        return True

    @staticmethod
    def is_in_check(board, color):
        """Check if the king of given color is in check"""
        # Find king position
        king_pos = None
        for pos, piece in board.items():
            if piece["type"] == "king" and piece["color"] == color:
                king_pos = pos
                break
        
        if not king_pos:
            return False
        
        # Check if any enemy piece can attack the king
        enemy_color = "black" if color == "white" else "white"
        for pos, piece in board.items():
            if piece["color"] == enemy_color:
                if ChessEngine.is_valid_move(board, pos, king_pos, enemy_color):
                    return True
        
        return False

    @staticmethod
    def get_all_valid_moves(board, color):
        """Get all valid moves for a color"""
        moves = []
        for pos, piece in board.items():
            if piece["color"] == color:
                for file in range(8):
                    for rank in range(8):
                        to_pos = ChessEngine.coords_to_pos(file, rank)
                        if to_pos != pos and ChessEngine.is_valid_move(board, pos, to_pos, color):
                            # Test if move puts own king in check
                            test_board = board.copy()
                            if to_pos in test_board:
                                del test_board[to_pos]
                            test_board[to_pos] = test_board[pos].copy()
                            del test_board[pos]
                            
                            if not ChessEngine.is_in_check(test_board, color):
                                moves.append((pos, to_pos))
        
        return moves


# Bot AI
class ChessBot:
    def __init__(self, difficulty=1):
        self.difficulty = difficulty

    def get_best_move(self, board, color):
        """Get the best move for the bot"""
        valid_moves = ChessEngine.get_all_valid_moves(board, color)
        if not valid_moves:
            return None
        
        if self.difficulty <= 2:
            return random.choice(valid_moves)
        elif self.difficulty <= 5:
            return self._get_moderate_move(board, valid_moves, color)
        else:
            return self._get_advanced_move(board, valid_moves, color)

    def _get_moderate_move(self, board, valid_moves, color):
        """Moderate difficulty: prefer captures and center control"""
        scored_moves = []
        
        for from_pos, to_pos in valid_moves:
            score = 0
            
            # Prefer captures
            if to_pos in board:
                piece_values = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9, "king": 100}
                score += piece_values.get(board[to_pos]["type"], 0) * 10
            
            # Prefer center control
            to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
            if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                score += 2
            
            scored_moves.append((score, from_pos, to_pos))
        
        scored_moves.sort(reverse=True)
        best_moves = [move for move in scored_moves if move[0] == scored_moves[0][0]]
        _, from_pos, to_pos = random.choice(best_moves)
        return from_pos, to_pos

    def _get_advanced_move(self, board, valid_moves, color):
        """Advanced difficulty: use minimax-like evaluation"""
        best_score = float('-inf')
        best_moves = []
        
        for from_pos, to_pos in valid_moves:
            score = self._evaluate_move(board, from_pos, to_pos, color)
            if score > best_score:
                best_score = score
                best_moves = [(from_pos, to_pos)]
            elif score == best_score:
                best_moves.append((from_pos, to_pos))
        
        return random.choice(best_moves)

    def _evaluate_move(self, board, from_pos, to_pos, color):
        """Evaluate a move's strength"""
        score = 0
        piece_values = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9, "king": 100}
        
        # Material gain
        if to_pos in board:
            score += piece_values.get(board[to_pos]["type"], 0) * 100
        
        # Position improvement
        piece = board[from_pos]
        if piece["type"] == "pawn":
            to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
            if color == "white":
                score += to_rank * 5  # Advance pawns
            else:
                score += (7 - to_rank) * 5
        
        # Center control
        to_file, to_rank = ChessEngine.pos_to_coords(to_pos)
        if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
            score += 10
        
        return score


# API Routes
@api_router.get("/bots", response_model=List[Bot])
async def get_bots():
    """Get list of available bots"""
    bots = [
        Bot(name="Rookie", difficulty=1, description="Just learning the rules"),
        Bot(name="Beginner", difficulty=2, description="Makes basic moves"),
        Bot(name="Apprentice", difficulty=3, description="Understands basic tactics"),
        Bot(name="Student", difficulty=4, description="Knows opening principles"),
        Bot(name="Club Player", difficulty=5, description="Decent tactical vision"),
        Bot(name="Tournament Player", difficulty=6, description="Strong positional play"),
        Bot(name="Expert", difficulty=7, description="Advanced tactical skills"),
        Bot(name="Master", difficulty=8, description="Deep strategic understanding"),
        Bot(name="Grandmaster", difficulty=9, description="World-class chess mind"),
        Bot(name="Chess Engine", difficulty=10, description="Near-perfect play")
    ]
    return bots

@api_router.post("/games", response_model=Game)
async def create_game(game_data: GameCreate):
    """Create a new chess game"""
    game = Game(
        mode=game_data.mode,
        white_player=game_data.white_player,
        black_player=game_data.black_player,
        board_state=ChessEngine.create_initial_board()
    )
    
    game_dict = game.dict()
    game_dict["created_at"] = game_dict["created_at"].isoformat()
    game_dict["last_move_at"] = game_dict["last_move_at"].isoformat()
    
    await db.games.insert_one(game_dict)
    return game

@api_router.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    """Get a specific game"""
    game_data = await db.games.find_one({"id": game_id})
    if not game_data:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Convert datetime strings back to datetime objects
    if isinstance(game_data.get("created_at"), str):
        game_data["created_at"] = datetime.fromisoformat(game_data["created_at"])
    if isinstance(game_data.get("last_move_at"), str):
        game_data["last_move_at"] = datetime.fromisoformat(game_data["last_move_at"])
    
    return Game(**game_data)

@api_router.post("/games/{game_id}/moves")
async def make_move(game_id: str, move_request: MoveRequest):
    """Make a move in the game"""
    game_data = await db.games.find_one({"id": game_id})
    if not game_data:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Convert datetime strings back to datetime objects for processing
    if isinstance(game_data.get("created_at"), str):
        game_data["created_at"] = datetime.fromisoformat(game_data["created_at"])
    if isinstance(game_data.get("last_move_at"), str):
        game_data["last_move_at"] = datetime.fromisoformat(game_data["last_move_at"])
    
    game = Game(**game_data)
    
    if game.game_status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game is not in progress")
    
    # Validate move
    if not ChessEngine.is_valid_move(game.board_state, move_request.from_pos, move_request.to_pos, game.current_turn):
        raise HTTPException(status_code=400, detail="Invalid move")
    
    # Make the move
    piece = game.board_state[move_request.from_pos].copy()
    captured_piece = None
    
    if move_request.to_pos in game.board_state:
        captured_piece = game.board_state[move_request.to_pos]["type"]
    
    # Update board
    game.board_state[move_request.to_pos] = piece
    game.board_state[move_request.to_pos]["has_moved"] = True
    del game.board_state[move_request.from_pos]
    
    # Handle pawn promotion
    if piece["type"] == "pawn" and move_request.promotion_piece:
        to_file, to_rank = ChessEngine.pos_to_coords(move_request.to_pos)
        if (piece["color"] == "white" and to_rank == 7) or (piece["color"] == "black" and to_rank == 0):
            game.board_state[move_request.to_pos]["type"] = move_request.promotion_piece
    
    # Record move
    move = Move(
        from_pos=move_request.from_pos,
        to_pos=move_request.to_pos,
        piece_type=piece["type"],
        captured_piece=captured_piece,
        promotion_piece=move_request.promotion_piece
    )
    game.moves_history.append(move)
    
    # Switch turns
    game.current_turn = PieceColor.BLACK if game.current_turn == PieceColor.WHITE else PieceColor.WHITE
    game.last_move_at = datetime.now()
    
    # Check for checkmate or stalemate
    valid_moves = ChessEngine.get_all_valid_moves(game.board_state, game.current_turn)
    if not valid_moves:
        if ChessEngine.is_in_check(game.board_state, game.current_turn):
            # Checkmate
            game.game_status = GameStatus.FINISHED
            game.winner = PieceColor.BLACK if game.current_turn == PieceColor.WHITE else PieceColor.WHITE
        else:
            # Stalemate
            game.game_status = GameStatus.FINISHED
    
    # Update database
    game_dict = game.dict()
    game_dict["created_at"] = game_dict["created_at"].isoformat()
    game_dict["last_move_at"] = game_dict["last_move_at"].isoformat()
    
    await db.games.update_one({"id": game_id}, {"$set": game_dict})
    
    return {"success": True, "game": game}

@api_router.post("/games/{game_id}/bot-move")
async def make_bot_move(game_id: str, difficulty: int = 5):
    """Make a bot move in the game"""
    game_data = await db.games.find_one({"id": game_id})
    if not game_data:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Convert datetime strings back to datetime objects for processing
    if isinstance(game_data.get("created_at"), str):
        game_data["created_at"] = datetime.fromisoformat(game_data["created_at"])
    if isinstance(game_data.get("last_move_at"), str):
        game_data["last_move_at"] = datetime.fromisoformat(game_data["last_move_at"])
    
    game = Game(**game_data)
    
    if game.game_status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game is not in progress")
    
    # Get bot move
    bot = ChessBot(difficulty)
    bot_move = bot.get_best_move(game.board_state, game.current_turn)
    
    if not bot_move:
        raise HTTPException(status_code=400, detail="No valid moves available")
    
    from_pos, to_pos = bot_move
    
    # Make the bot move
    move_request = MoveRequest(
        game_id=game_id,
        from_pos=from_pos,
        to_pos=to_pos
    )
    
    return await make_move(game_id, move_request)

@api_router.get("/games")
async def get_games():
    """Get all games"""
    games = await db.games.find().to_list(1000)
    for game in games:
        if isinstance(game.get("created_at"), str):
            game["created_at"] = datetime.fromisoformat(game["created_at"])
        if isinstance(game.get("last_move_at"), str):
            game["last_move_at"] = datetime.fromisoformat(game["last_move_at"])
    
    return [Game(**game) for game in games]


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
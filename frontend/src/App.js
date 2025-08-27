import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PIECE_SYMBOLS = {
  white: {
    king: '♔',
    queen: '♕',
    rook: '♖',
    bishop: '♗',
    knight: '♘',
    pawn: '♙'
  },
  black: {
    king: '♚',
    queen: '♛',
    rook: '♜',
    bishop: '♝',
    knight: '♞',
    pawn: '♟'
  }
};

const INITIAL_BOARD = {
  "a8": { type: "rook", color: "black" },
  "b8": { type: "knight", color: "black" },
  "c8": { type: "bishop", color: "black" },
  "d8": { type: "queen", color: "black" },
  "e8": { type: "king", color: "black" },
  "f8": { type: "bishop", color: "black" },
  "g8": { type: "knight", color: "black" },
  "h8": { type: "rook", color: "black" },
  "a7": { type: "pawn", color: "black" },
  "b7": { type: "pawn", color: "black" },
  "c7": { type: "pawn", color: "black" },
  "d7": { type: "pawn", color: "black" },
  "e7": { type: "pawn", color: "black" },
  "f7": { type: "pawn", color: "black" },
  "g7": { type: "pawn", color: "black" },
  "h7": { type: "pawn", color: "black" },
  "a2": { type: "pawn", color: "white" },
  "b2": { type: "pawn", color: "white" },
  "c2": { type: "pawn", color: "white" },
  "d2": { type: "pawn", color: "white" },
  "e2": { type: "pawn", color: "white" },
  "f2": { type: "pawn", color: "white" },
  "g2": { type: "pawn", color: "white" },
  "h2": { type: "pawn", color: "white" },
  "a1": { type: "rook", color: "white" },
  "b1": { type: "knight", color: "white" },
  "c1": { type: "bishop", color: "white" },
  "d1": { type: "queen", color: "white" },
  "e1": { type: "king", color: "white" },
  "f1": { type: "bishop", color: "white" },
  "g1": { type: "knight", color: "white" },
  "h1": { type: "rook", color: "white" }
};

const ChessBoard = ({ game, onMove, selectedSquare, onSquareClick, lastMove, isPlayerTurn }) => {
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
  const ranks = [8, 7, 6, 5, 4, 3, 2, 1];

  const isLightSquare = (file, rank) => {
    return (files.indexOf(file) + rank) % 2 === 0;
  };

  const isHighlighted = (position) => {
    return selectedSquare === position || 
           (lastMove && (lastMove.from_pos === position || lastMove.to_pos === position));
  };

  return (
    <div className="chess-board">
      {ranks.map(rank =>
        files.map(file => {
          const position = `${file}${rank}`;
          const piece = game?.board_state?.[position];
          const isLight = isLightSquare(file, rank);
          const highlighted = isHighlighted(position);
          const selected = selectedSquare === position;

          return (
            <div
              key={position}
              className={`square ${isLight ? 'light' : 'dark'} ${highlighted ? 'highlighted' : ''} ${selected ? 'selected' : ''} ${!isPlayerTurn ? 'disabled' : ''}`}
              onClick={() => isPlayerTurn && onSquareClick(position)}
            >
              <div className="square-label">{position}</div>
              {piece && (
                <div className="piece">
                  {PIECE_SYMBOLS[piece.color][piece.type]}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

const GameInfo = ({ game, onNewGame, onBotMove, bots, selectedBot, onBotSelect }) => {
  const currentPlayer = game?.current_turn === 'white' ? game?.white_player : game?.black_player;
  const isGameFinished = game?.game_status === 'finished';
  
  return (
    <div className="game-info">
      <div className="game-status">
        <h3>Chess Game</h3>
        {game && (
          <div className="status-details">
            <p><strong>Mode:</strong> {game.mode === 'pvp' ? 'Player vs Player' : 'Player vs Bot'}</p>
            <p><strong>White:</strong> {game.white_player}</p>
            <p><strong>Black:</strong> {game.black_player}</p>
            <p><strong>Current Turn:</strong> 
              <span className={`turn-indicator ${game.current_turn}`}>
                {game.current_turn} ({currentPlayer})
              </span>
            </p>
            {isGameFinished && (
              <div className="game-result">
                {game.winner ? (
                  <p className="winner">🏆 Winner: {game.winner} ({game.winner === 'white' ? game.white_player : game.black_player})</p>
                ) : (
                  <p className="draw">🤝 Game ended in a draw</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {game?.mode === 'pvb' && game?.current_turn === 'black' && !isGameFinished && (
        <div className="bot-controls">
          <h4>Bot Turn</h4>
          <div className="bot-selector">
            <label>Select Bot Difficulty:</label>
            <select 
              value={selectedBot} 
              onChange={(e) => onBotSelect(parseInt(e.target.value))}
              className="bot-select"
            >
              {bots.map(bot => (
                <option key={bot.difficulty} value={bot.difficulty}>
                  {bot.name} (Level {bot.difficulty}) - {bot.description}
                </option>
              ))}
            </select>
          </div>
          <button 
            onClick={() => onBotMove(selectedBot)}
            className="bot-move-btn"
          >
            Make Bot Move
          </button>
        </div>
      )}

      <div className="game-controls">
        <button onClick={() => onNewGame('pvp')} className="new-game-btn">
          New PvP Game
        </button>
        <button onClick={() => onNewGame('pvb')} className="new-game-btn">
          New vs Bot Game
        </button>
      </div>

      {game?.moves_history?.length > 0 && (
        <div className="move-history">
          <h4>Move History</h4>
          <div className="moves-list">
            {game.moves_history.slice(-10).map((move, index) => (
              <div key={index} className="move-item">
                {move.piece_type} {move.from_pos} → {move.to_pos}
                {move.captured_piece && ` (captured ${move.captured_piece})`}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const PromotionModal = ({ isOpen, onSelect, onClose }) => {
  if (!isOpen) return null;

  const pieces = ['queen', 'rook', 'bishop', 'knight'];

  return (
    <div className="promotion-modal-overlay">
      <div className="promotion-modal">
        <h3>Choose promotion piece:</h3>
        <div className="promotion-pieces">
          {pieces.map(piece => (
            <button
              key={piece}
              onClick={() => onSelect(piece)}
              className="promotion-piece-btn"
            >
              {PIECE_SYMBOLS.white[piece]}
              <br />
              {piece}
            </button>
          ))}
        </div>
        <button onClick={onClose} className="close-btn">Cancel</button>
      </div>
    </div>
  );
};

function App() {
  const [currentGame, setCurrentGame] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [bots, setBots] = useState([]);
  const [selectedBot, setSelectedBot] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPromotion, setShowPromotion] = useState(false);
  const [pendingMove, setPendingMove] = useState(null);

  // Load bots on component mount
  useEffect(() => {
    const loadBots = async () => {
      try {
        const response = await axios.get(`${API}/bots`);
        setBots(response.data);
      } catch (err) {
        console.error('Error loading bots:', err);
        setError('Failed to load bots');
      }
    };

    loadBots();
  }, []);

  const createNewGame = async (mode) => {
    setLoading(true);
    setError(null);
    
    try {
      const gameData = {
        mode: mode,
        white_player: "Player 1",
        black_player: mode === 'pvp' ? "Player 2" : "Bot"
      };

      const response = await axios.post(`${API}/games`, gameData);
      setCurrentGame(response.data);
      setSelectedSquare(null);
    } catch (err) {
      console.error('Error creating game:', err);
      setError('Failed to create new game');
    } finally {
      setLoading(false);
    }
  };

  const handleSquareClick = useCallback((position) => {
    if (!currentGame || currentGame.game_status === 'finished') return;

    // If this is a bot game and it's black's turn, don't allow moves
    if (currentGame.mode === 'pvb' && currentGame.current_turn === 'black') return;

    if (!selectedSquare) {
      // Select a piece
      const piece = currentGame.board_state[position];
      if (piece && piece.color === currentGame.current_turn) {
        setSelectedSquare(position);
      }
    } else {
      // Try to move the selected piece
      if (selectedSquare === position) {
        // Deselect if clicking the same square
        setSelectedSquare(null);
      } else {
        // Check if it's a pawn promotion move
        const piece = currentGame.board_state[selectedSquare];
        const isPromotion = piece?.type === 'pawn' && 
          ((piece.color === 'white' && position[1] === '8') ||
           (piece.color === 'black' && position[1] === '1'));

        if (isPromotion) {
          setPendingMove({ from: selectedSquare, to: position });
          setShowPromotion(true);
        } else {
          makeMove(selectedSquare, position);
        }
        setSelectedSquare(null);
      }
    }
  }, [currentGame, selectedSquare]);

  const makeMove = async (fromPos, toPos, promotionPiece = null) => {
    if (!currentGame) return;

    setLoading(true);
    setError(null);

    try {
      const moveData = {
        game_id: currentGame.id,
        from_pos: fromPos,
        to_pos: toPos,
        promotion_piece: promotionPiece
      };

      const response = await axios.post(`${API}/games/${currentGame.id}/moves`, moveData);
      setCurrentGame(response.data.game);
    } catch (err) {
      console.error('Error making move:', err);
      setError(err.response?.data?.detail || 'Invalid move');
    } finally {
      setLoading(false);
    }
  };

  const makeBotMove = async (difficulty) => {
    if (!currentGame) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API}/games/${currentGame.id}/bot-move?difficulty=${difficulty}`);
      setCurrentGame(response.data.game);
    } catch (err) {
      console.error('Error making bot move:', err);
      setError(err.response?.data?.detail || 'Bot move failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePromotionSelect = (piece) => {
    if (pendingMove) {
      makeMove(pendingMove.from, pendingMove.to, piece);
      setPendingMove(null);
      setShowPromotion(false);
    }
  };

  const isPlayerTurn = () => {
    if (!currentGame || currentGame.game_status === 'finished') return false;
    if (currentGame.mode === 'pvp') return true;
    return currentGame.current_turn === 'white'; // In PvB mode, player is always white
  };

  const lastMove = currentGame?.moves_history?.[currentGame.moves_history.length - 1];

  return (
    <div className="App">
      <div className="chess-container">
        <div className="chess-game">
          <div className="board-container">
            <ChessBoard
              game={currentGame}
              onMove={makeMove}
              selectedSquare={selectedSquare}
              onSquareClick={handleSquareClick}
              lastMove={lastMove}
              isPlayerTurn={isPlayerTurn()}
            />
            
            {loading && (
              <div className="loading-overlay">
                <div className="loading-spinner">Making move...</div>
              </div>
            )}
          </div>

          <GameInfo
            game={currentGame}
            onNewGame={createNewGame}
            onBotMove={makeBotMove}
            bots={bots}
            selectedBot={selectedBot}
            onBotSelect={setSelectedBot}
          />
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <PromotionModal
          isOpen={showPromotion}
          onSelect={handlePromotionSelect}
          onClose={() => {
            setShowPromotion(false);
            setPendingMove(null);
          }}
        />

        <div className="app-info">
          <h1>♔ Chess Master ♛</h1>
          <p>Play chess against AI bots or challenge a friend!</p>
          <ul>
            <li>✓ Complete chess rules implementation</li>
            <li>✓ 10 AI difficulty levels (Rookie to Chess Engine)</li>
            <li>✓ Player vs Player mode</li>
            <li>✓ Beautiful interactive chess board</li>
            <li>✓ Move history and game status</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
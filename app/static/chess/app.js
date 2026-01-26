const boardElement = document.getElementById('board');
const statusElement = document.getElementById('status');
const analysisElement = document.getElementById('analysis-output');
const resetBtn = document.getElementById('reset-btn');

let game = new Chess();
let selectedSquare = null;

const pieceImages = {
    'wP': 'https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg',
    'wN': 'https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg',
    'wB': 'https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg',
    'wR': 'https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg',
    'wQ': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg',
    'wK': 'https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg',
    'bP': 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg',
    'bN': 'https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg',
    'bB': 'https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg',
    'bR': 'https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg',
    'bQ': 'https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg',
    'bK': 'https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg'
};

function createBoard() {
    boardElement.innerHTML = '';
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const square = document.createElement('div');
            square.className = `square ${(r + c) % 2 === 0 ? 'light' : 'dark'}`;
            const id = String.fromCharCode(97 + c) + (8 - r);
            square.id = id;
            square.onclick = () => onSquareClick(id);
            boardElement.appendChild(square);
        }
    }
    updateBoard();
}

function updateBoard() {
    const squares = document.querySelectorAll('.square');
    squares.forEach(sq => {
        sq.innerHTML = '';
        const piece = game.get(sq.id);
        if (piece) {
            const pieceDiv = document.createElement('div');
            pieceDiv.className = 'piece';
            pieceDiv.style.backgroundImage = `url(${pieceImages[piece.color + piece.type.toUpperCase()]})`;
            sq.appendChild(pieceDiv);
        }
    });
}

async function onSquareClick(id) {
    if (game.turn() === 'b' || game.game_over()) return;

    if (selectedSquare === id) {
        selectedSquare = null;
        clearHighlights();
        return;
    }

    // If source square is already selected, try to move
    if (selectedSquare) {
        const move = game.move({
            from: selectedSquare,
            to: id,
            promotion: 'q'
        });

        if (move) {
            selectedSquare = null;
            clearHighlights();
            updateBoard();
            handleTurnChange();
            return;
        }
    }

    // Select piece if it's player's turn and square has user's piece
    const piece = game.get(id);
    if (piece && piece.color === 'w') {
        selectedSquare = id;
        highlightSquare(id);
    }
}

function handleTurnChange() {
    if (game.game_over()) {
        statusElement.innerText = "Game Over!";
        return;
    }

    if (game.turn() === 'b') {
        statusElement.innerText = "Bot is thinking...";
        document.getElementById('turn-indicator').className = 'indicator black';
        makeBotMove();
    } else {
        statusElement.innerText = "Your Turn";
        document.getElementById('turn-indicator').className = 'indicator white';
    }
}

async function makeBotMove() {
    try {
        const response = await fetch('/chess/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fen: game.fen() })
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        const uciMove = data.move;

        // Parse UCI move (e.g., e7e5)
        const from = uciMove.substring(0, 2);
        const to = uciMove.substring(2, 4);

        game.move({ from, to, promotion: 'q' });
        updateBoard();

        // Log bot thinking process (mock for now as API response is simple)
        analysisElement.innerText = "Bot plays: " + uciMove;

        handleTurnChange();
    } catch (e) {
        console.error(e);
        statusElement.innerText = "Error contacting Bot!";
    }
}

function highlightSquare(id) {
    clearHighlights();
    document.getElementById(id).classList.add('selected');
    const moves = game.moves({ square: id, verbose: true });
    moves.forEach(m => {
        document.getElementById(m.to).classList.add('valid-move');
    });
}

function clearHighlights() {
    document.querySelectorAll('.square').forEach(sq => {
        sq.classList.remove('selected', 'valid-move');
    });
}

resetBtn.onclick = () => {
    game = new Chess();
    selectedSquare = null;
    clearHighlights();
    updateBoard();
    handleTurnChange();
    analysisElement.innerText = "Start a game to see bot predictions...";
};

// Start
createBoard();

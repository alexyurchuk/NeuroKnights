using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PlayerInput : MonoBehaviour
{
    GameManager gameManager;
    BoardUI boardUI;
    Board board;
    MovesHandler movesHandler;
    UIManager uiManager;

    Coord selectedCoord = null; // Tracks the selected piece
    Coord currentCoord;         // Tracks the highlighted cell with WASD
<<<<<<< HEAD
    CurrentSelection SelectedText;
    bool mouseDown = false;
=======

>>>>>>> f6d0fa815f0314b8511df34cc351c4332471931a
    bool selected = false;

    private int currentMoveIndex; // Tracks the currently highlighted move during move selection
    private List<Move> moves; // Stores legal moves for the selected piece

    private void Start()
    {
        gameManager = GetComponent<GameManager>();
        board = GetComponent<Board>();
        movesHandler = GetComponent<MovesHandler>();
        uiManager = GetComponent<UIManager>();
        boardUI = FindObjectOfType<BoardUI>();

        // Initialize currentCoord based on player's turn
        currentCoord = gameManager.isWhitesTurn ? new Coord(7, 7) : new Coord(0, 7);
        HighlightCurrentCell();
    }

    private void Update()
    {
        // Handle keyboard inputs
        if (gameManager.gameMode != GameManager.GameMode.Local && gameManager.isWhitesTurn != gameManager.startPlayerIsWhite)
        {
            return;
        }

<<<<<<< HEAD
        // if (Input.GetMouseButtonDown(0))
        // {
        //     OnMouseDown();
        // }

        // if (Input.GetMouseButtonUp(0))
        // {
        //     OnMouseUp();
        // }

        // if (mouseDown)
        // {
        //     OnMouseMove();
        // }

        HandleWASDInput(); // Add WASD input handling
=======
        if (Input.GetKeyDown(KeyCode.W))
        {
            MoveUp();
        }
        else if (Input.GetKeyDown(KeyCode.S))
        {
            MoveDown();
        }
        else if (Input.GetKeyDown(KeyCode.A))
        {
            MoveLeft();
        }
        else if (Input.GetKeyDown(KeyCode.D))
        {
            MoveRight();
        }
        else if (Input.GetKeyDown(KeyCode.E)) // Assume E is the select key
        {
            Select();
        }
        else if (Input.GetKeyDown(KeyCode.Q))
        {
            Deselect();
        }
>>>>>>> f6d0fa815f0314b8511df34cc351c4332471931a
    }

    // Public methods for external socket commands
    public void MoveUp()
    {
        if (!selected){
            if (gameManager.isWhitesTurn){
                HandlePieceSelection(1, 0);
            }
            else{
                HandlePieceSelection(-1, 0);
            }
        }
        else{
            HandleMoveSelection(1);
        }
    }

    public void MoveDown()
    {
        if (!selected)
        {
            if (gameManager.isWhitesTurn)
            {
                HandlePieceSelection(-1, 0);
            }
            else
            {
                HandlePieceSelection(1, 0);
            }
        }
        else
        {
            HandleMoveSelection(-1);
        }
    }

    public void MoveLeft()
    {
        if (!selected)
        {
            if (gameManager.isWhitesTurn)
            {
                HandlePieceSelection(0, -1);
            }
            else
            {
                HandlePieceSelection(0, 1);
            }
        }
    }

    public void MoveRight()
    {
        if (!selected)
        {
            if (gameManager.isWhitesTurn)
            {
                HandlePieceSelection(0, 1);
            }
            else
            {
                HandlePieceSelection(0, -1);
            }
        }
    }

    public void Select()
    {
        if (!selected)
        {
            selected = true;
            SelectCoord(currentCoord);
            moves = movesHandler.GetLegalMoves(board, currentCoord, gameManager.isWhitesTurn);
            currentMoveIndex = 0;
            if (moves != null && moves.Count > 0)
            {
                HighlightMove(moves[currentMoveIndex].to);
            }
        }
        else
        {
            TryMoveToCoord(moves[currentMoveIndex].to);
            selected = false;
            DeselectCoord();
        }
    }

    public void Deselect()
    {
        selected = false;
        DeselectCoord();
        HighlightCurrentCell();
    }

    // Core logic for piece selection
    private void HandlePieceSelection(int fileDelta, int rankDelta)
    {
        bool moved = MoveToNextPiece(fileDelta, rankDelta);
        if (moved) HighlightCurrentCell();
    }

    // Core logic for move selection
    private void HandleMoveSelection(int direction)
    {
        if (moves == null || moves.Count == 0)
        {
            selected = false;
            DeselectCoord();
            HighlightCurrentCell();
            return;
        }

        currentMoveIndex = (currentMoveIndex + direction + moves.Count) % moves.Count;
        HighlightMove(moves[currentMoveIndex].to);
    }

    private void HighlightMove(Coord coord)
    {
        boardUI.ResetAllSquareColors();
        SelectCoord(selectedCoord);
        boardUI.SelectSquare(coord); // Highlight the selected move square
    }

    private bool MoveToNextPiece(int fileDelta, int rankDelta)
    {
        int file = currentCoord.file;
        int rank = currentCoord.rank;

        if (fileDelta != 0) // Moving vertically (W or S)
        {
            while (true)
            {
                file += fileDelta;
                if (file < 0 || file > 7) return false;

                int piece = board.GetPieceFromCoord(new Coord(rank, file));
                if (piece != Piece.Empty && Piece.PieceColor(piece) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
                {
                    currentCoord = new Coord(rank, file);
                    boardUI.ResetAllSquareColors();
                    return true;
                }
            }
        }
        else if (rankDelta != 0) // Moving horizontally (A or D)
        {
            while (true)
            {
                rank += rankDelta;
                if (rank < 0 || rank > 7) return false;

                for (file = currentCoord.file; file >= 0 && file <= 7; file += rankDelta)
                {
                    int piece = board.GetPieceFromCoord(new Coord(rank, file));
                    if (piece != Piece.Empty && Piece.PieceColor(piece) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
                    {
                        currentCoord = new Coord(rank, file);
                        boardUI.ResetAllSquareColors();
                        return true;
                    }
                }
                for (file = currentCoord.file; file >= 0 && file <= 7; file -= rankDelta)
                {
                    int piece = board.GetPieceFromCoord(new Coord(rank, file));
                    if (piece != Piece.Empty && Piece.PieceColor(piece) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
                    {
                        currentCoord = new Coord(rank, file);
                        boardUI.ResetAllSquareColors();
                        return true;
                    }
                }
            }
        }

        return false;
    }

    private void HighlightCurrentCell()
    {
        boardUI.SelectSquare(currentCoord);
        SelectedText.CurrentMove(currentCoord);

    }

<<<<<<< HEAD
    // private void OnMouseDown()
    // {
    //     mouseDown = true;

    //     Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);

    //     if (TryGetSquare(mousePos, out Coord coord))
    //     {
    //         int pieceFromCoord = board.GetPieceFromCoord(coord);

    //         // We have a piece selected, so we want to move it
    //         if (selectedCoord != null)
    //         {
    //             // Try to move to coord
    //             if (TryMoveToCoord(coord)) return;

    //             // If clicked on own piece and it isn't same, select it
    //             if (pieceFromCoord != Piece.Empty && Piece.PieceColor(pieceFromCoord) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black) && (coord.rank != selectedCoord.rank || coord.file != selectedCoord.file))
    //             {
    //                 SelectCoord(coord);
    //             }
    //             // Deselect coord
    //             else DeselectCoord();
    //         }
    //         // We don't have a piece selected, so we want to select it if it's the right player's turn
    //         else if (Piece.PieceColor(pieceFromCoord) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
    //         {
    //             SelectCoord(coord);
    //         }
    //     }
    //     // Clicked outside board, so deselect
    //     else DeselectCoord();
    // }

    // private void OnMouseMove()
    // {
    //     Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);

    //     if (selectedCoord == null) return;

    //     SpriteRenderer pieceRenderer = boardUI.pieceRenderers[selectedCoord.rank, selectedCoord.file];
    //     pieceRenderer.transform.position = new Vector3(mousePos.x, mousePos.y, -pieceRenderer.transform.forward.z * 2);
    // }

    // private void OnMouseUp()
    // {
    //     mouseDown = false;

    //     if (selectedCoord == null) return;

    //     SpriteRenderer pieceRenderer = boardUI.pieceRenderers[selectedCoord.rank, selectedCoord.file];
    //     pieceRenderer.transform.localPosition = -pieceRenderer.transform.forward;

    //     Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
    //     if (TryGetSquare(mousePos, out Coord coord))
    //     {
    //         if (coord.rank != selectedCoord.rank || coord.file != selectedCoord.file)
    //         {
    //             TryMoveToCoord(coord);
    //         }
    //     }
    // }

=======
>>>>>>> f6d0fa815f0314b8511df34cc351c4332471931a
    private void SelectCoord(Coord coord)
    {
        selectedCoord = coord;
        boardUI.ResetAllSquareColors();
        boardUI.SelectSquare(selectedCoord);

        List<Move> moves = movesHandler.GetLegalMoves(board, coord, gameManager.isWhitesTurn);
        if (moves != null)
        {
            boardUI.HighlightLegalSquares(moves);
        }
    }

    private void DeselectCoord()
    {
        boardUI.ResetAllSquareColors();
        selectedCoord = null;
    }

    private bool TryMoveToCoord(Coord coord)
    {
        List<Move> moves = movesHandler.GetLegalMoves(board, selectedCoord, gameManager.isWhitesTurn);
        if (moves != null)
        {
            foreach (Move move in moves)
            {
                if (move.to.rank == coord.rank && move.to.file == coord.file)
                {
                    board.MovePiece(move);

                    if (board.CanPromote(coord))
                    {
                        uiManager.OpenPromotionMenu(coord);
                        return true;
                    }
                    gameManager.MoveMade();
                    gameManager.FlipBoard();
                    return true;
                }
            }
        }

        return false;
    }
    public void PromoteAfterInput(Coord coord, int piece)
    {
        board.Promote(coord, piece);

        selectedCoord = null;

        gameManager.MoveMade();
    }
}
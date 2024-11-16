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

    bool mouseDown = false;

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
        if (gameManager.gameMode != GameManager.GameMode.Local && gameManager.isWhitesTurn != gameManager.startPlayerIsWhite)
        {
            return;
        }

        if (Input.GetMouseButtonDown(0))
        {
            OnMouseDown();
        }

        if (Input.GetMouseButtonUp(0))
        {
            OnMouseUp();
        }

        if (mouseDown)
        {
            OnMouseMove();
        }

        HandleWASDInput(); // Add WASD input handling
    }

    private void HandleWASDInput()
    {
        bool moved = false;

        // Reset highlight on the previously selected cell

        // Capture WASD input
        if (Input.GetKeyDown(KeyCode.W)) // Move up
        {
            moved = MoveToNextPiece(1, 0);
            boardUI.ResetAllSquareColors();
        }
        else if (Input.GetKeyDown(KeyCode.S)) // Move down
        {
            moved = MoveToNextPiece(-1, 0);
            boardUI.ResetAllSquareColors();
        }
        else if (Input.GetKeyDown(KeyCode.A)) // Move left
        {
            moved = MoveToNextPiece(0, -1);
            boardUI.ResetAllSquareColors();
        }
        else if (Input.GetKeyDown(KeyCode.D)) // Move right
        {
            moved = MoveToNextPiece(0, 1);
            boardUI.ResetAllSquareColors();
        }

        if (moved)
        {
            HighlightCurrentCell();
        }
    }

    private bool MoveToNextPiece(int fileDelta, int rankDelta)
    {
        int file = currentCoord.file;
        int rank = currentCoord.rank;

        Debug.Log($"Starting search from (rank: {rank}, file: {file})");

        // Determine the search direction
        bool searchingColumns = fileDelta != 0; // True if moving horizontally (A/D), false for vertical (W/S)

        while (true)
        {
            // Update position
            file += fileDelta;
            rank += rankDelta;

            // If out of bounds, shift to the next column or row
            if (file < 0 || file > 7 || rank < 0 || rank > 7)
            {
                Debug.Log($"Out of bounds at (rank: {rank}, file: {file}). Shifting to next row/column.");

 
                    // Move to the next column, reset rank to 0 or 7
                    file += fileDelta > 0 ? 1 : -1;
                    rank = fileDelta > 0 ? 0 : 7;
        

                // Stop if out of bounds entirely
                if (file < 0 || file > 7 || rank < 0 || rank > 7)
                {
                    Debug.Log("Entire board searched. No valid piece found.");
                    return false;
                }

                Debug.Log($"Shifted to (rank: {rank}, file: {file})");
            }

            Debug.Log($"Checking (rank: {rank}, file: {file})");

            // Check for a piece of the current player's color
            int piece = board.GetPieceFromCoord(new Coord(rank, file));
            if (piece != Piece.Empty && Piece.PieceColor(piece) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
            {
                Debug.Log($"Piece found at (rank: {rank}, file: {file})");
                currentCoord = new Coord(rank, file);
                return true;
            }
        }
    }



    private void HighlightCurrentCell()
    {
        // Highlight the cell at the currentCoord
        boardUI.SelectSquare(currentCoord);
    }

    private void OnMouseDown()
    {
        mouseDown = true;

        Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);

        if (TryGetSquare(mousePos, out Coord coord))
        {
            int pieceFromCoord = board.GetPieceFromCoord(coord);

            // We have a piece selected, so we want to move it
            if (selectedCoord != null)
            {
                // Try to move to coord
                if (TryMoveToCoord(coord)) return;

                // If clicked on own piece and it isn't same, select it
                if (pieceFromCoord != Piece.Empty && Piece.PieceColor(pieceFromCoord) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black) && (coord.rank != selectedCoord.rank || coord.file != selectedCoord.file))
                {
                    SelectCoord(coord);
                }
                // Deselect coord
                else DeselectCoord();
            }
            // We don't have a piece selected, so we want to select it if it's the right player's turn
            else if (Piece.PieceColor(pieceFromCoord) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
            {
                SelectCoord(coord);
            }
        }
        // Clicked outside board, so deselect
        else DeselectCoord();
    }

    private void OnMouseMove()
    {
        Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);

        if (selectedCoord == null) return;

        SpriteRenderer pieceRenderer = boardUI.pieceRenderers[selectedCoord.rank, selectedCoord.file];
        pieceRenderer.transform.position = new Vector3(mousePos.x, mousePos.y, -pieceRenderer.transform.forward.z * 2);
    }

    private void OnMouseUp()
    {
        mouseDown = false;

        if (selectedCoord == null) return;

        SpriteRenderer pieceRenderer = boardUI.pieceRenderers[selectedCoord.rank, selectedCoord.file];
        pieceRenderer.transform.localPosition = -pieceRenderer.transform.forward;

        Vector2 mousePos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
        if (TryGetSquare(mousePos, out Coord coord))
        {
            if (coord.rank != selectedCoord.rank || coord.file != selectedCoord.file)
            {
                TryMoveToCoord(coord);
            }
        }
    }

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
        // If move is legal
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

                    selectedCoord = null;
                    gameManager.MoveMade();

                    return true;
                }
            }
        }

        return false;
    }

    public bool TryGetSquare(Vector2 pos, out Coord coord)
    {
        int rank = Mathf.RoundToInt(pos.x + 3.5f);
        int file = Mathf.RoundToInt(pos.y + 3.5f);

        if (gameManager.boardFlipped)
        {
            rank = 7 - rank;
            file = 7 - file;
        }

        coord = new Coord(rank, file);

        if (rank < 0 || rank > 7 || file < 0 || file > 7)
        {
            return false;
        }

        return true;
    }

    public void PromoteAfterInput(Coord coord, int piece)
    {
        board.Promote(coord, piece);

        selectedCoord = null;

        gameManager.MoveMade();
    }
}

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
    CurrentSelection SelectedText;
    bool mouseDown = false;
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
        if (gameManager.gameMode != GameManager.GameMode.Local && gameManager.isWhitesTurn != gameManager.startPlayerIsWhite)
        {
            return;
        }

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
    }

    private void HandleWASDInput() //Piece and move Selection 
    {
        bool moved = false;

        // Piece Selection
        if(!selected)
        {
        if(gameManager.gameMode == GameManager.GameMode.Local){ //If gameplay is doubleplayer (Local)
            if(gameManager.isWhitesTurn){ //If white's turn, normal 
                if (Input.GetKeyDown(KeyCode.W)) // Move up
                {
                    moved = MoveToNextPiece(1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.S)) // Move down
                {
                    moved = MoveToNextPiece(-1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.A)) // Move left
                {
                    moved = MoveToNextPiece(0, -1);
                }
                else if (Input.GetKeyDown(KeyCode.D)) // Move right
                {
                    moved = MoveToNextPiece(0, 1);
                }
                else if (Input.GetKeyDown(KeyCode.E)) // Select
                {
                    selected = true;
                    SelectCoord(currentCoord);
                    moves = movesHandler.GetLegalMoves(board, currentCoord, gameManager.isWhitesTurn);
                    currentMoveIndex = 0;
                    HighlightMove(moves[currentMoveIndex].to);
                }
            }
            else{ //If black's turn, inverse controls.
                if (Input.GetKeyDown(KeyCode.W)) // Move up
                {
                    moved = MoveToNextPiece(-1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.S)) // Move down
                {
                    moved = MoveToNextPiece(1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.A)) // Move left
                {
                    moved = MoveToNextPiece(0, 1);
                }
                else if (Input.GetKeyDown(KeyCode.D)) // Move right
                {
                    moved = MoveToNextPiece(0, -1);
                }
                else if (Input.GetKeyDown(KeyCode.E)) // Select
                {
                    selected = true;
                    SelectCoord(currentCoord);
                    moves = movesHandler.GetLegalMoves(board, currentCoord, gameManager.isWhitesTurn);
                    currentMoveIndex = 0;
                    HighlightMove(moves[currentMoveIndex].to);
                }
             }
            }
           else{ //Computer gameplay, only should stay as white (bottom)
            if (Input.GetKeyDown(KeyCode.W)) // Move up
                {
                    moved = MoveToNextPiece(1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.S)) // Move down
                {
                    moved = MoveToNextPiece(-1, 0);
                }
                else if (Input.GetKeyDown(KeyCode.A)) // Move left
                {
                    moved = MoveToNextPiece(0, -1);
                }
                else if (Input.GetKeyDown(KeyCode.D)) // Move right
                {
                    moved = MoveToNextPiece(0, 1);
                }
                else if (Input.GetKeyDown(KeyCode.E)) // Select
                {
                    selected = true;
                    SelectCoord(currentCoord);
                    moves = movesHandler.GetLegalMoves(board, currentCoord, gameManager.isWhitesTurn);
                    currentMoveIndex = 0;
                    HighlightMove(moves[currentMoveIndex].to);
                }
           }      
        }
        // Move Selection
        else
        {
            if (moves == null || moves.Count == 0)
            {
                Debug.LogError("No moves to navigate!");
                selected = false;
                DeselectCoord();
                HighlightCurrentCell();
                return;
            }
            if(gameManager.gameMode == GameManager.GameMode.Local){ //If gameplay is doubleplayer (Local)
                if(gameManager.isWhitesTurn){ //White's turn, move selecting
                    if (Input.GetKeyDown(KeyCode.W))
                    {
                        currentMoveIndex = (currentMoveIndex + 1) % moves.Count;
                        HighlightMove(moves[currentMoveIndex].to);
                    }
                    else if (Input.GetKeyDown(KeyCode.S)) // Navigate down through moves
                    {
                        currentMoveIndex = (currentMoveIndex - 1 + moves.Count) % moves.Count;
                        HighlightMove(moves[currentMoveIndex].to);
                    }
                    else if (Input.GetKeyDown(KeyCode.E)) // Confirm move
                    {
                        TryMoveToCoord(moves[currentMoveIndex].to);
                        selected = false;
                    }
                    else if (Input.GetKeyDown(KeyCode.Q)) // Cancel move selection
                    {
                        selected = false;
                        DeselectCoord();
                        HighlightCurrentCell(); // Go back to piece selection
                    }
                }
                else{ //Black's turn, move selecting 
                    if (Input.GetKeyDown(KeyCode.W))
                    {
                        currentMoveIndex = (currentMoveIndex + 1) % moves.Count;
                        HighlightMove(moves[currentMoveIndex].to);
                    }
                    else if (Input.GetKeyDown(KeyCode.S)) // Navigate down through moves
                    {
                        currentMoveIndex = (currentMoveIndex - 1 + moves.Count) % moves.Count;
                        HighlightMove(moves[currentMoveIndex].to);
                    }
                    else if (Input.GetKeyDown(KeyCode.E)) // Confirm move
                    {
                        TryMoveToCoord(moves[currentMoveIndex].to);
                        selected = false;
                    }
                    else if (Input.GetKeyDown(KeyCode.Q)) // Cancel move selection
                    {
                        selected = false;
                        DeselectCoord();
                        HighlightCurrentCell(); // Go back to piece selection
                    }
                }
            }
            else{ //move selection, computer gameplay
                if (Input.GetKeyDown(KeyCode.W))
                {
                    currentMoveIndex = (currentMoveIndex + 1) % moves.Count;
                    HighlightMove(moves[currentMoveIndex].to);
                }
                else if (Input.GetKeyDown(KeyCode.S)) // Navigate down through moves
                {
                    currentMoveIndex = (currentMoveIndex - 1 + moves.Count) % moves.Count;
                    HighlightMove(moves[currentMoveIndex].to);
                }
                else if (Input.GetKeyDown(KeyCode.E)) // Confirm move
                {
                    TryMoveToCoord(moves[currentMoveIndex].to);
                    selected = false;
                }
                else if (Input.GetKeyDown(KeyCode.Q)) // Cancel move selection
                {
                    selected = false;
                    DeselectCoord();
                    HighlightCurrentCell(); // Go back to piece selection
                }
            }
            
            
        }

        if (moved)
        {
            HighlightCurrentCell();
        }
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

        Debug.Log($"Starting search from (rank: {rank}, file: {file})");

        if (fileDelta != 0) // Moving vertically (W or S)
        {
            while (true)
            {
                Debug.Log("vertical");
                file += fileDelta; // Move up or down (file is vertical)

                // Wrap around or stop if out of bounds
                if (file < 0 || file > 7)
                {
                    Debug.Log("No valid pieces found in any column.");
                    return false;
                }

                // Check if the current square contains a valid piece
                int piece = board.GetPieceFromCoord(new Coord(rank, file));
                if (piece != Piece.Empty && Piece.PieceColor(piece) == (gameManager.isWhitesTurn ? Piece.White : Piece.Black))
                {
                    Debug.Log($"Piece found at (rank: {rank}, file: {file})");
                    currentCoord = new Coord(rank, file);
                    boardUI.ResetAllSquareColors();
                    return true;
                }

                Debug.Log($"No valid pieces in column {file}. Moving to the next column.");
            }
        }
        else if (rankDelta != 0) // Moving horizontally (A or D)
        {
            while (true)
            {
                Debug.Log("horizontal");
                rank += rankDelta; // Move left or right (rank is horizontal)

                // Stop if out of bounds
                if (rank < 0 || rank > 7)
                {
                    Debug.Log("Reached the left or right of the board.");
                    return false;
                }

                // Check the column for the topmost piece
                if (gameManager.isWhitesTurn)
                {
                    // Check the column for the topmost piece (White)
                    for (file = 7; file >= 0; file--) // Top to bottom
                    {
                        int piece = board.GetPieceFromCoord(new Coord(rank, file));
                        if (piece != Piece.Empty && Piece.PieceColor(piece) == Piece.White)
                        {
                            Debug.Log($"White piece found at (rank: {rank}, file: {file})");
                            currentCoord = new Coord(rank, file);
                            boardUI.ResetAllSquareColors();
                            return true;
                        }
                    }
                }
                else
                {
                    // Check the column for the bottommost piece (Black)
                    for (file = 0; file <= 7; file++) // Bottom to top
                    {
                        int piece = board.GetPieceFromCoord(new Coord(rank, file));
                        if (piece != Piece.Empty && Piece.PieceColor(piece) == Piece.Black)
                        {
                            Debug.Log($"Black piece found at (rank: {rank}, file: {file})");
                            currentCoord = new Coord(rank, file);
                            boardUI.ResetAllSquareColors();
                            return true;
                        }
                    }
                }
                
            }
        }

        return false; // Fallback case (shouldn't happen)
    }

    private void HighlightCurrentCell()
    {
        // Highlight the cell at the currentCoord
        boardUI.SelectSquare(currentCoord);
        SelectedText.CurrentMove(currentCoord);

    }

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
                    if(gameManager.gameMode == GameManager.GameMode.Local){
                         gameManager.FlipBoard();
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
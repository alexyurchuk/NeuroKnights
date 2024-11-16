using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// Represents a scriptable object to define a theme for the chess game.
// This includes colors for the board, pieces, and other visual settings.
public class Theme : ScriptableObject
{
    // Colors for the normal chessboard squares (light and dark) 
    public Color lightColor, darkColor;
    public Sprite dotSprite;
    public Sprite circleSprite; 
    // Colors used when a square is selected (for both light and dark squares)
    public Color lightSelectedColor, darkSelectedColor;

    // Colors for highlighting legal moves (light and dark squares) TODO:  This is what needs to be changed, dots 
    public Color lightLegalColor, darkLegalColor;

    // A material that can be applied to unlit objects (like board squares)
    public Material unlit;

    // Sprites for white and black chess pieces, grouped in a custom class
    public PieceSprites whitePieceSprites, blackPieceSprites;

    // Method to get the correct piece sprite based on the piece type.
    // Accepts an integer representing the piece.
    public Sprite GetPieceSprite(int piece)
    {
        // Return null if the piece is empty (no piece on the square)
        if (piece == Piece.Empty)
        {
            return null;
        }

        // Determine if the piece is white or black
        bool isWhite = piece < Piece.Black;

        // Use the appropriate sprites (white or black) based on the piece color
        PieceSprites pieceSprites = isWhite ? whitePieceSprites : blackPieceSprites;

        // Adjust the piece type to account for color offsets
        piece = isWhite ? piece - Piece.White : piece - Piece.Black;

        // Return the correct sprite for the piece type
        return pieceSprites.GetSprite(piece);
    }
}

// Represents a collection of sprites for different chess pieces
[System.Serializable]
public class PieceSprites
{
    // Sprites for each type of chess piece
    public Sprite pawn, knight, bishop, rook, queen, king;

    // Method to get the sprite for a specific piece type
    public Sprite GetSprite(int piece)
    {
        // Determine which sprite to return based on the piece type
        switch (piece)
        {
            case Piece.Pawn:
                return pawn;
            case Piece.Knight:
                return knight;
            case Piece.Bishop:
                return bishop;
            case Piece.Rook:
                return rook;
            case Piece.Queen:
                return queen;
            case Piece.King:
                return king;
            default:
                return null; // Return null if the piece type is invalid
        }
    }
}
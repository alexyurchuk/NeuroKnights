using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public static class Piece
{
    public const int OutOfBounds = -1;
    public const int Empty = 0;
    public const int Pawn = 1;
    public const int Knight = 2;
    public const int Bishop = 3;
    public const int Rook = 4;
    public const int Queen = 5;
    public const int King = 6;

    public const int White = 10;
    public const int Black = 20;

    public static int PieceColor(int piece)
    {
        return piece == OutOfBounds ? OutOfBounds : piece == Empty ? Empty : piece < Black ? White : Black;
    }

    public static int PieceType(int piece)
    {
        return piece == OutOfBounds ? OutOfBounds : piece == Empty ? Empty : piece < Black ? piece - White : piece - Black;
    }

    // Existing method to convert piece to FEN character
    public static string PieceToFenChar(int piece)
    {
        switch (piece)
        {
            case Pawn + White: return "P";
            case Pawn + Black: return "p";
            case Knight + White: return "N";
            case Knight + Black: return "n";
            case Bishop + White: return "B";
            case Bishop + Black: return "b";
            case Rook + White: return "R";
            case Rook + Black: return "r";
            case Queen + White: return "Q";
            case Queen + Black: return "q";
            case King + White: return "K";
            case King + Black: return "k";
            default: return "";
        }
    }

    // New method to convert piece type to string (like "Pawn", "Knight", etc.)
    public static string PieceTypeToString(int piece)
    {
        switch (PieceType(piece))
        {
            case Pawn: return "Pawn";
            case Knight: return "Knight";
            case Bishop: return "Bishop";
            case Rook: return "Rook";
            case Queen: return "Queen";
            case King: return "King";
            default: return "Unknown";  // If piece type is undefined
        }
    }
}

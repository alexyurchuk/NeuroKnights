using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class BoardUI : MonoBehaviour
{
    GameObject[,] squareDots = new GameObject[8, 8];
    GameObject[,] squareCircle = new GameObject[8,8];
    // GameManager reference
    GameManager gm;

    // Assigned in editor
    public Theme theme;
    public GameObject numberPrefab;

    // Mesh and sprite renderers
    MeshRenderer[,] squareRenderers;
    public SpriteRenderer[,] pieceRenderers;
    public float ScaleFactor = 0.5f; //determins how small the board is
    private void Start(){
        // Get GameManager
        gm = FindObjectOfType<GameManager>();
    }

    public void CreateBoardUI(){
        // Create empty mesh and sprite renderers
        squareRenderers = new MeshRenderer[8, 8];
        pieceRenderers = new SpriteRenderer[8, 8];
        
        // Loop through ranks and files
        for (int rank = 0; rank < 8; rank++)
        {
            for (int file = 0; file < 8; file++)
            {
                // Get coord
                Coord coord = new Coord(rank, file);
                
                // Create square
                Transform square = GameObject.CreatePrimitive(PrimitiveType.Quad).transform;
                square.gameObject.name = $"Square {GetSquareName(coord)}";
                square.SetParent(transform.GetChild(0));
                square.localScale = new Vector3(ScaleFactor,ScaleFactor,1);
                square.position = GetPosFromCoord(coord) * ScaleFactor; // 0.5 

                // Create mesh on square
                MeshRenderer mr = square.GetComponent<MeshRenderer>();
                mr.material = theme.unlit;
                mr.material.color = (rank + file) % 2 == 0 ? theme.lightColor : theme.darkColor;
                squareRenderers[rank, file] = mr;

                // Create sprite in square, i.e creating piece 
                SpriteRenderer sr = new GameObject("Piece").AddComponent<SpriteRenderer>();
                sr.transform.SetParent(square);
                sr.transform.localScale = Vector3.one * 0.2f * ScaleFactor;
                sr.transform.localPosition = -sr.transform.forward;
                pieceRenderers[rank, file] = sr;

                 // Create dot for available moves (initially hidden)
                GameObject dot = new GameObject("Dot");
                SpriteRenderer dotRenderer = dot.AddComponent<SpriteRenderer>();
                dotRenderer.sprite = theme.dotSprite;  //Dot Sprite
                dotRenderer.transform.SetParent(square);
                dotRenderer.transform.localScale = Vector3.one * 0.3f * ScaleFactor;  // Adjust dot size
                dotRenderer.transform.localPosition = -dotRenderer.transform.forward; // Place it at the center of the square
                Color currentDotAlpha = dotRenderer.color; // Get the current color
                currentDotAlpha.a = 0.5f;                  // Set the alpha (0.0f to 1.0f)

                dotRenderer.color = currentDotAlpha;  
            
                dotRenderer.enabled = true; 

                GameObject Circle = new GameObject("Circle");
                SpriteRenderer CircleRenderer = Circle.AddComponent<SpriteRenderer>();
                CircleRenderer.sprite = theme.circleSprite; //Circle sprite
                CircleRenderer.transform.SetParent(square);
                CircleRenderer.transform.localScale = Vector3.one * 0.3f * ScaleFactor;  // Adjust Circle size, original size, 0.3, currently at half 0.15
                CircleRenderer.transform.localPosition = -dotRenderer.transform.forward; // Place it at the center of the square
                Color currentCircleAlpha = CircleRenderer.color; // Get the current color
                currentCircleAlpha.a = 0.5f;                  // Set the alpha (0.0f to 1.0f)
                dotRenderer.color = currentCircleAlpha;  
            

                Debug.Log($"Dot sprite: {theme.dotSprite}"); //Test
                CircleRenderer.enabled = true; 
                
                squareCircle[rank, file] = Circle;
                squareDots[rank, file] = dot;
                // Add rank number to left side 1234...
                if (rank == 0){
                    TMP_Text fileText = Instantiate(numberPrefab).GetComponent<TMP_Text>();
                    fileText.transform.SetParent(square);
                    fileText.transform.localPosition = -fileText.transform.forward * ScaleFactor;
                    fileText.text = (file + 1).ToString();
                    fileText.transform.SetParent(transform.GetChild(1)); 
                    fileText.gameObject.name = "File " + (file + 1).ToString();
                }

                // Add rank character to bottom ABCD...
                if (file == 0){
                    TMP_Text rankText = Instantiate(numberPrefab).GetComponent<TMP_Text>();
                    rankText.transform.SetParent(square);
                    rankText.transform.localPosition = -rankText.transform.forward * ScaleFactor;
                    rankText.text = ((char)(rank + 65)).ToString();
                    rankText.alignment = TextAlignmentOptions.BottomRight;
                    rankText.transform.SetParent(transform.GetChild(1));
                    rankText.gameObject.name = "Rank " + ((char)(rank + 65)).ToString();
                }
            }
        }
    }

    public void UpdateBoard(Board board, bool flipBoard){
        // Rotate board if flipped 
        transform.GetChild(0).localRotation = Quaternion.Euler(0, 0, flipBoard ? 180 : 0);

        // Loop through board squares
        for (int i = 0; i < board.squares.Length; i++)
        {
            // Get coord
            Coord coord = new Coord(i % 8, i / 8);
            // Update piece on coord
            UpdatePiece(coord, board.GetPieceFromCoord(coord), flipBoard);
        }
    }

    public void UpdatePiece(Coord coord, int piece, bool flipped){
        // Get piece sprite from theme
        Sprite sprite = theme.GetPieceSprite(piece);
        // Get sprite renderer on coord
        SpriteRenderer renderer = pieceRenderers[coord.rank, coord.file];

        if (renderer != null){
            // Assign sprite
            renderer.sprite = sprite;
            // Rotate if board is flipped
            renderer.transform.localRotation = Quaternion.Euler(flipped ? 180 : 0, flipped ? 180 : 0, 0);
        }
    }

    public void SelectSquare(Coord coord){
        // Set square color to selected theme color
        squareRenderers[coord.rank, coord.file].material.color = (coord.rank + coord.file) % 2 == 0 ? theme.lightSelectedColor : theme.darkSelectedColor;
    }

    public void DeselectSquare(Coord coord){
        // Reset square color to theme color
        squareRenderers[coord.rank, coord.file].material.color = (coord.rank + coord.file) % 2 == 0 ? theme.lightColor : theme.darkColor;
    }

    public void HighlightLegalSquares(List<Move> moves){
    if (moves == null) return;
    
    // Loop through legal moves
    foreach (Move move in moves)
    {
        // Check that it's inside the array
        if (move.to.rank < 0 || move.to.rank > 7 || move.to.file < 0 || move.to.file > 7) continue;
        // Show dot or circle (if theres a piece) on legal square
            if (pieceRenderers[move.to.rank, move.to.file].sprite != null) {
                
                // There's a piece on the square at the given coord
                squareCircle[move.to.rank, move.to.file].SetActive(true);
                }
            else {
                //No piece
                squareDots[move.to.rank, move.to.file].SetActive(true);
            }
      
 
        
        // Set the square color for legal moves (slashed for now) 
        //squareRenderers[move.to.rank, move.to.file].material.color = (move.to.rank + move.to.file) % 2 == 0 ? theme.lightLegalColor : theme.darkLegalColor;
            
    }
}

    public void ResetAllSquareColors(){
    // Loop through all squares
    for (int rank = 0; rank < 8; rank++)
    {
        for (int file = 0; file < 8; file++)
        {
            // Reset square color to theme color
            squareRenderers[rank, file].material.color = 
                (rank + file) % 2 == 0 ? theme.lightColor : theme.darkColor;
            
            // Hide the dot for this square
            squareDots[rank, file].SetActive(false);
            squareCircle[rank,file].SetActive(false);
        }
    }
}

    private Vector3 GetPosFromCoord(Coord coord, int depth = 0){
        return new Vector3(coord.rank - 3.5f, coord.file - 3.5f, -depth);
    }

    public string GetSquareName(Coord coord){
        char fileLetter = (char)(coord.file + 65);
        return $"{fileLetter}{coord.rank + 1}";
    }

    public void VisualizeBoard(Board board){
        for (int rank = 7; rank >= 0; rank--)
        {
            string line = "";
            for (int file = 0; file < 8; file++)
            {
                line += Piece.PieceToFenChar(board.squares[rank * 8 + file]) + "\t";
            }
            Debug.Log(line);
        }
    }
}

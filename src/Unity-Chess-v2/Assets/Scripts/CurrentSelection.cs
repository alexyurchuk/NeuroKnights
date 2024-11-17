using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro; // Import the TextMeshPro namespace

public class CurrentSelection : MonoBehaviour
{
    public TextMeshProUGUI text; // Reference to the TextMeshProUGUI component

    void Start()
    {
        // Automatically find the TextMeshProUGUI component attached to this GameObject or any child
        text = GetComponentInChildren<TextMeshProUGUI>();

        if (text == null) {
            Debug.LogError("TextMeshProUGUI component not found!");
        }
    }

    // Method to update the text based on the given Coord
    public void CurrentMove(Coord coord)
    {
        if (text != null) {
            text.text = coord.ToString(); // Set the text to the string representation of Coord
        }
        else {
            Debug.LogError("TextMeshProUGUI component is missing!");
        }
    }
}
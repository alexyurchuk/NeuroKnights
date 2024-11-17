using UnityEngine;
using UnityEngine.UI;

public class Flasher : MonoBehaviour
{
    public float frequency = 10f; // Frequency in Hz
    private float flashInterval; // Time interval between flashes
    private float timer;         // Timer to track the intervals

    private Image flasherImage;  // Reference to the Image component
    private bool isWhite = false; // Track current state

    void Start()
    {
        // Calculate the interval for flashing
        flashInterval = 1f / (2f * frequency); // Divide by 2 for black-white-black cycle
        flasherImage = GetComponent<Image>();
    }

    void Update()
    {
        timer += Time.deltaTime;

        // If timer exceeds the flash interval, toggle the state
        if (timer >= flashInterval)
        {
            timer -= flashInterval; // Reset timer
            ToggleColor();
        }
    }

    void ToggleColor()
    {
        isWhite = !isWhite;
        flasherImage.color = isWhite ? Color.white : Color.black;
    }
}

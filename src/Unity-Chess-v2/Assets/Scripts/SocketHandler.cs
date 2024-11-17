using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using UnityEngine.UI;

public class SocketHandler : MonoBehaviour
{
    public Text ConnectionStatus;
    private TcpClient client;
    private NetworkStream stream;
    private Thread receiveThread;
    private bool isRunning = false;

    void Start()
    {
        ConnectToPython("127.0.0.1", 65432); // Adjust IP and port as needed
    }

    private void Update()
    {
        if(Input.GetKeyDown(KeyCode.R))
            ConnectToPython("127.0.0.1", 65432);
    }

    /// <summary>
    /// Connects to the Python server.
    /// </summary>
    /// <param name="ip">The server IP address.</param>
    /// <param name="port">The server port.</param>
    public void ConnectToPython(string ip, int port)
    {
        ConnectionStatus.text = "Connecting...";
        ConnectionStatus.color = Color.yellow;

        try
        {
            client = new TcpClient(ip, port);
            stream = client.GetStream();
            isRunning = true;
            receiveThread = new Thread(ReceiveData);
            receiveThread.Start();
            Debug.Log("Connected to Python server.");
            ConnectionStatus.text = "Connected!";
            ConnectionStatus.color = Color.green;
        }
        catch (Exception e)
        {
            Debug.LogError($"Connection failed: {e.Message}"); 
            ConnectionStatus.text = "Connection failed. Press R to retry.";
            ConnectionStatus.color = Color.red;
        }
    }

    /// <summary>
    /// Sends a string message to the Python server.
    /// </summary>
    /// <param name="message">The message to send.</param>
    public void SendMessageToPython(string message)
    {
        if (stream != null && client.Connected)
        {
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
                Debug.Log($"Sent to Python: {message}");
            }
            catch (Exception e)
            {
                Debug.LogError($"Error sending message: {e.Message}");
            }
        }
    }

    /// <summary>
    /// Receives data from the Python server and processes it.
    /// </summary>
    private void ReceiveData()
    {
        try
        {
            byte[] buffer = new byte[1024];
            while (isRunning)
            {
                if (stream != null && stream.DataAvailable)
                {
                    int bytesRead = stream.Read(buffer, 0, buffer.Length);
                    string receivedMessage = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    Debug.Log($"Received from Python: {receivedMessage}");
                    ProcessInput(receivedMessage);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error receiving data: {e.Message}");
        }
    }

    /// <summary>
    /// Processes the received string to check if it matches W, A, S, or D.
    /// </summary>
    /// <param name="input">The received input string.</param>
    private void ProcessInput(string input)
    {
        switch (input.ToUpper())
        {
            case "W":
                Debug.Log("Move Up");
                break;
            case "A":
                Debug.Log("Move Left");
                break;
            case "S":
                Debug.Log("Move Down");
                break;
            case "D":
                Debug.Log("Move Right");
                break;
            default:
                Debug.Log($"Unhandled input: {input}");
                break;
        }
    }

    /// <summary>
    /// Cleans up resources when the application quits.
    /// </summary>
    void OnApplicationQuit()
    {
        isRunning = false;
        receiveThread?.Join();
        stream?.Close();
        client?.Close();
        Debug.Log("Disconnected from Python server.");
        ConnectionStatus.text = "Not Connected to Server";
        ConnectionStatus.color = Color.red;
    }
}

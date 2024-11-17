using System;
using System.Collections.Generic;
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
    public GameObject gameManager;
    private PlayerInput playerInput;

    private readonly object queueLock = new object();
    private Queue<Action> mainThreadActions = new Queue<Action>();

    void Start()
    {
        playerInput = gameManager.GetComponent<PlayerInput>();
        ConnectToPython("127.0.0.1", 65432); // Adjust IP and port as needed
    }

    private void Update()
    {
        // Process any queued actions on the main thread
        lock (queueLock)
        {
            while (mainThreadActions.Count > 0)
            {
                var action = mainThreadActions.Dequeue();
                action.Invoke();
            }
        }

        if (Input.GetKeyDown(KeyCode.R))
            ConnectToPython("127.0.0.1", 65432);
    }

    public void ConnectToPython(string ip, int port)
    {
        EnqueueMainThreadAction(() =>
        {
            ConnectionStatus.text = "Connecting...";
            ConnectionStatus.color = Color.yellow;
        });

        try
        {
            client = new TcpClient(ip, port);
            stream = client.GetStream();
            isRunning = true;
            receiveThread = new Thread(ReceiveData);
            receiveThread.Start();
            Debug.Log("Connected to Python server.");
            EnqueueMainThreadAction(() =>
            {
                ConnectionStatus.text = "Connected!";
                ConnectionStatus.color = Color.green;
            });
        }
        catch (Exception e)
        {
            Debug.LogError($"Connection failed: {e.Message}");
            EnqueueMainThreadAction(() =>
            {
                ConnectionStatus.text = "Connection failed. Press R to retry.";
                ConnectionStatus.color = Color.red;
            });
        }
    }

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
                    EnqueueMainThreadAction(() => ProcessInput(receivedMessage));
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error receiving data: {e.Message}");
        }
    }

    private void ProcessInput(string input)
    {
        switch (input.ToUpper())
        {
            case "W":
                playerInput.MoveUp();
                break;
            case "A":
                playerInput.MoveLeft();
                break;
            case "S":
                playerInput.MoveRight();
                break;
            case "D":
                playerInput.MoveDown();
                break;
            case "E":
                playerInput.Select();
                break;
            case "Q":
                playerInput.Deselect();
                break;
            default:
                Debug.Log($"Unhandled input: {input}");
                break;
        }
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        receiveThread?.Join();
        stream?.Close();
        client?.Close();
        Debug.Log("Disconnected from Python server.");
        EnqueueMainThreadAction(() =>
        {
            ConnectionStatus.text = "Not Connected to Server";
            ConnectionStatus.color = Color.red;
        });
    }

    private void EnqueueMainThreadAction(Action action)
    {
        lock (queueLock)
        {
            mainThreadActions.Enqueue(action);
        }
    }
}

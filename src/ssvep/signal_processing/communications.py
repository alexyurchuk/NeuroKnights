import socket
import threading

class SocketServer:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.address = None
        self.running = False  # Indicates if the server is running
        self.client_connected = False  # Indicates if a client is connected
        self.lock = threading.Lock()  # For thread safety

    def start_server(self):
        """Starts the server and waits for a connection."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.running = True  # Server is now running
        print("Server is listening...")
        self.connection, self.address = self.server_socket.accept()
        print(f"Connected to {self.address}")
        self.client_connected = True  # Client is connected
        # Start the receive thread after connection is established
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def receive(self):
        """Continuously listens for messages from the client."""
        while self.client_connected:
            try:
                if self.connection:
                    data = self.connection.recv(1024)
                    if data:
                        message = data.decode()
                        print(f"Received: {message}")
                    else:
                        print("No data received. Closing connection.")
                        self.client_connected = False
                        self.connection.close()
                        break
            except Exception as e:
                print(f"Error in receive thread: {e}")
                self.client_connected = False

    def send(self, message):
        """Sends a message to the client."""
        with self.lock:
            if self.connection and self.client_connected:
                try:
                    self.connection.sendall(message.encode())
                    print(f"Sent: {message}")
                except Exception as e:
                    print(f"Error sending message: {e}")
            else:
                print("No client connected. Cannot send message.")

    def close_connection(self):
        """Closes the server connection."""
        self.client_connected = False
        self.running = False
        if self.connection:
            self.connection.close()
        self.server_socket.close()
        print("Server closed.")

    def run(self):
        """Starts the server in a separate thread."""
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()
        return server_thread

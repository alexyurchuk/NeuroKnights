import socket
import threading


class SocketServer:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.address = None
        self.running = False

    def start_server(self):
        """Starts the server and waits for a connection."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print("Server is listening...")
        self.connection, self.address = self.server_socket.accept()
        print(f"Connected to {self.address}")
        self.running = True

    def receive(self):
        """Continuously listens for messages from the client in a thread."""
        while self.running:
            try:
                if self.connection:
                    data = self.connection.recv(1024)
                    if data:
                        message = data.decode()
                        print(f"Received: {message}")
                    else:
                        print("No data received. Closing connection.")
                        self.running = False
                        break
            except Exception as e:
                print(f"Error in receive thread: {e}")
                self.running = False

    def send(self, message):
        """Sends a message to the client."""
        if self.connection:
            try:
                self.connection.sendall(message.encode())
                print(f"Sent: {message}")
            except Exception as e:
                print(f"Error sending message: {e}")

    def close_connection(self):
        """Closes the server connection."""
        self.running = False
        if self.connection:
            self.connection.close()
        self.server_socket.close()
        print("Server closed.")

    def run(self):
        """Starts the server and runs the receive thread."""
        self.start_server()
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        return receive_thread


if __name__ == "__main__":
    server = SocketServer()

    try:
        receive_thread = server.run()

        while server.running:
            # Server can send messages manually
            to_send = input("Enter message to send: ")
            if to_send.lower() == "exit":
                break
            server.send(to_send)
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server.close_connection()

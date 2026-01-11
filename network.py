import socket
import pickle

class Network:
    """
    Simple LAN networking.
    One player hosts, one player joins.
    Use send(state_dict) to send/receive game state.
    """
    def __init__(self, host=False, ip=""):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

        if host:
            self.sock.bind(("0.0.0.0", 5555))
            self.sock.listen(1)
            print("Waiting for opponent...")
            self.conn, _ = self.sock.accept()
            print("Opponent connected!")
        else:
            self.sock.connect((ip, 5555))
            self.conn = self.sock

    def send(self, data):
        self.conn.send(pickle.dumps(data))
        reply = self.conn.recv(4096)
        return pickle.loads(reply)

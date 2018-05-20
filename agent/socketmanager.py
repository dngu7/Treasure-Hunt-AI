
import socket


class TCPSocketManager:
    def __init__(self, ip_address, port_no, view_size):
        self.ip_address = ip_address
        self.port_no = port_no
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address,port_no))
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.map_size = view_size ** 2
    
    def send_action(self, total_actions):
        new_message = total_actions.encode()
        self.sock.send(new_message)	

    def recv_data(self):
        total_message = ''
        while len(total_message) < (self.map_size - 1):
            recv_message = self.sock.recv(4000)
            total_message = total_message + recv_message.decode()
        return list(total_message)
        
    def recv_map(self):
        map_data = self.recv_data()
        k = 0

        for i in range(self.view_size):
            for j in range(self.view_size):
                if not ((i == 2) and (j == 2)):
                    self.view_window[i][j] = map_data[k]
                    k += 1
        return self.view_window    


if __name__ == '__main__':
    TCPSocketManager.__init__()
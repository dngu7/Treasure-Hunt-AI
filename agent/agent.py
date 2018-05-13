#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #
import socket
import sys
import pickle

class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]

    def get_action(self):
        valid_actions = 'FLRCUBflrcub'
        input_actions = input("Enter Action(s): ")
        for action in input_actions:
            if action in valid_actions:
                return action
        return 0

    def print_view(self):
        print("\n+{}+".format("-" * self.view_size))
        for i in range(self.view_size):
            print('|', end = '')
            for j in range(self.view_size):
                if (i == 2) and (j == 2):
                    print('^', end = '')
                else:
                    print(self.view_window[i][j], end = '')
            print('|')
        print("+{}+\n".format("-" * self.view_size))
        return 0

    def main_loop(self):
        while (True):
            self.view_window = self.TCP_Socket.recv_map()
            self.print_view()
            self.get_action()
                
            

class TCPSocketManager:
    def __init__(self, ip_address, port_no, view_size):
        self.ip_address = ip_address
        self.port_no = port_no
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address,port_no))
        #self.sd = self.sock.makefile( 'rw', 0 )
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
    
    def send_action(self, action):
        #new_message = pickle.dumps(action)
        action = action.encode()
        self.sock.send(action)	
        #try:
        #    self.sd.write(action)
        #    self.sd.flush()
        #except KeyboardInterrupt:
        #    raise
        #return True

    def recv_data(self):
        msg = ""
        msglen = self.view_size ** 2
        try:
            while len(msg) != msglen:
                data = self.sd.read( min(2048, msglen - len(msg)) )
                if not len(data):
                    break
                msg = msg + data
        except KeyboardInterrupt:
            raise
        return msg

    def recv_data2(self):
        recv_message = self.sock.recv(4096)
        decode_message = recv_message.decode().split(' ')
        print(decode_message)

        return decode_message

        
    def recv_map(self):
        map_data = self.recv_data2()
        
        for map_piece in map_data:
            for i in range(self.view_size):
                for j in range(self.view_size):
                    if (i != 2) and (j != 2):
                        self.view_window[i][j] = map_piece

        return self.view_window    

    def close(self):
        self.sock.close()
        self.sock = None


# Input: python3 Agent -p 31415
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no, view_size)
new_agent.main_loop()

        



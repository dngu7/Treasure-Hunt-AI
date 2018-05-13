#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #

import socket
import sys
import pickle
import time

class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]

    def get_action(self):
        valid_actions = 'FLRCUBflrcub'
        input_actions = input("Enter Action(s): ")
        final_actions = ''
        for action in input_actions:
            if action in valid_actions:
                final_actions = final_actions + action
        return final_actions

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
        time.sleep(1)
        while (True):
            self.view_window = self.TCP_Socket.recv_map()
            self.print_view()
            self.TCP_Socket.send_action(self.get_action())


class TCPSocketManager:
    def __init__(self, ip_address, port_no, view_size):
        self.ip_address = ip_address
        self.port_no = port_no
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address,port_no))
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.map_size = view_size ** 2
    
    def send_action(self, action):
        new_message = action.encode()
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



# Input: python3 Agent -p [port_no]
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no, view_size)
new_agent.main_loop()

        


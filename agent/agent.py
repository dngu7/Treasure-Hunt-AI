#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #

import socket
import sys
import pickle
import time
from rotation import rotate

class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.global_map = [['?'] * 160 for i in range(160)]
        self.items = {'k' : 0, 'o' : 0, 'a' : 0, 'r' : 0, '$' : 0}
        self.blocks = ['T','*','-']
        self.direction = 0
        self.position = [80,80]
        self.onRaft = 0
        self.requiredItems = {'-' : 'k', 'T' : 'a'}
    


    def update_global_map(self):
        rotated_view_window = rotate(self.view_window,360 - self.direction)

        N = 5
        M = 160
        
        # current position of a agent in the 
        # global map.
        curr_i = self.position[0] 
        curr_j = self.position[1]
        
        
        # looping around the view map to copy into
        # GlobalMap
        for i in range(N):
            for j in range(N):
                element = rotated_view_window[i][j]
                
                # indices to copy into global map.
                Iidx = curr_i + i - 2;
                Jidx = curr_j + j - 2;
                
            # Conditons for writing to gloabl map
            # 1) The copying indices should not
            # exceed the global map
            # 2) Not copying the current directions of AI.
                if  (Iidx >= 0 and Iidx < M and
                Jidx >= 0 and Jidx < M and
                    not (i == 2 and j == 2) ):
                        self.global_map[Iidx][Jidx] = element
                elif (i == 2 and j == 2):
                    self.global_map[Iidx][Jidx] = '^'
                    

                    
                
            # else if the current viewmap reading is at the centre,
            # that is stored as agent directions.  

  
    def move_agent(self, action):
        next_position = self.give_front_position(self.position)
        #print("{} ({}) next = {} : {}".format(self.position,self.direction, next_position, self.global_map[front_position[0]][front_position[1]]))

        if action == 'L' or action == 'l':
            self.direction = (self.direction + 90) % 360
        elif action == 'R' or action == 'r':
            self.direction = (self.direction - 90) % 360
        elif action == 'F' or action == 'f':
            
            if self.global_map[next_position[0]][next_position[1]] not in self.blocks:
                self.position = next_position

                element = self.global_map[next_position[0]][next_position[1]]

                if element in self.items:
                    self.items[element] += 1
                
                if element == '~':
                    if self.items['o'] > 0:
                        self.items['o'] -= 1
                    else:
                        self.items['r'] -= 1
                        self.onRaft = 1
                elif element == ' ':
                    self.onRaft = 0


        elif (action == 'C' or action == 'c'):
            tree = self.global_map[next_position[0]][next_position[1]]
            if tree == 'T' and self.items['a'] >= 1:
                self.items['r'] += 1
            

    def give_front_position(self, starting_position):
        new_position = starting_position.copy()
        if self.direction == 0:
            new_position[0] -= 1
        elif self.direction == 90:
            new_position[1] -= 1
        elif self.direction == 180:
            new_position[0] += 1
        elif self.direction == 270:
            new_position[1] += 1
        return new_position
        

    def get_action(self):
        valid_actions = 'FLRCUBflrcub'
        final_actions = ''
        while final_actions == '':
            input_actions = input("Enter Action(s): ")
            for action in input_actions:
                if action in valid_actions:
                    final_actions = final_actions + action

        return final_actions

    def print_matrix(self, matrix, print_size):
        print("\n+{}+".format("-" * print_size))
        for i in range(print_size):
            print('|', end = '')
            for j in range(print_size):
                if (i == 2) and (j == 2):
                    print('^', end = '')
                else:
                    print(matrix[i][j], end = '')
            print('|')
        print("+{}+\n".format("-" * print_size))
        return 0

    def main_loop(self):
        time.sleep(1)
        action_list = 'z'
        while (True):
            for i in range(len(action_list)):
                self.move_agent(action_list[i])
                self.view_window = self.TCP_Socket.recv_map()
                self.update_global_map()
                self.print_matrix(self.view_window, self.view_size)
                self.print_matrix(self.global_map, 160)
                print(self.position)
                print(self.items)
                
            action_list = self.get_action()
            self.TCP_Socket.send_action(action_list)


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



# Input: python3 Agent -p [port_no]
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no, view_size)
new_agent.main_loop()

        



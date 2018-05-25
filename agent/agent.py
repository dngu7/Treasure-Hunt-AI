#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #

import sys
import pickle
import time
from queue import Queue
from rotation import rotate
from socketmanager import TCPSocketManager
from astar import astarItems, AstarMap

class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.global_map_size = 160
        self.global_map = [['?'] * self.global_map_size for i in range(self.global_map_size)]
        self.global_map_values = [[0] * self.global_map_size for i in range(self.global_map_size)]
        self.astar_memory = [[[],[],[]] * self.global_map_size for i in range(self.global_map_size)]
        self.emptyitems = {'k' : 0, 'o' : 0, 'a' : 0, 'r' : 0, '$' : 0}
        self.items = {'k' : 0, 'o' : 0, 'a' : 0, 'r' : 0, '$' : 0}
        self.requiredItems = {'-' : 'k', 'T' : 'a'}
        self.blocks = ['T','*','-','.']
        self.direction = 0
        self.position = [80,80]
        self.home = [80,80]
        self.onRaft = 0
        self.onLand = 1
        self.actionQueue = Queue()
        self.rotationAngleTbl = {(-1,0): 0, (0,-1): 90, (1,0): 180, (0,1): 270}
        self.placedStonesList = []
        self.AstarMap = AstarMap(self.global_map)
        self.visibleCoordinates = [[78,78],[78,79],[78,80],[78,81],[78,82],[79,78],[79,79],[79,80],[79,81],[79,82],[80,78],[80,79],[80,81],[80,82],[81,78],[81,79],[81,80],[81,81],[81,82],[82,78],[82,79],[82,80],[82,81],[82,82]]
        self.exploredCoordinates = [[80,80]]

    def decideNextPosition(self):
        nextPosition = [80,80]
        points = -100000

        if self.items['$'] > 0:
            if self.decide_routehome(self.position):
                return nextPosition

        for coordinate in self.visibleCoordinates:
            i = coordinate[0]
            j = coordinate[1]
            if self.global_map_values[i][j] > points:
                points = self.global_map_values[i][j]
                nextPosition = [i,j]
                print('[{},{}] has higher points ({})'.format(i,j, self.global_map_values[i][j]))
            else:
                print('[{},{}] failed and has less points ({})'.format(i,j, self.global_map_values[i][j]))
        return nextPosition
        
    def check_routehome(self, startingpoint, treasurepoint):
        firsttripresult = astarItems(self.AstarMap,startingpoint, treasurepoint, self.items, self.onRaft)
        if len(firsttripresult[0]) > 0:
            hometripresult = astarItems(self.AstarMap, treasurepoint, self.home, firsttripresult[2], 0)
        else:
            return 0

        if len(hometripresult[0]) > 0:
            return 1
    
    def decide_routehome(self,startingpoint):
        astarresult = astarItems(self.AstarMap,startingpoint, self.home, self.items, 0)
        print('PathHome: {}'.format(astarresult))
        if len(astarresult[0]) > 0:
            if startingpoint == self.position:
                self.astar_memory[80][80] = astarresult
            return 1
        else:
            return 0
        
    def update_global_map_values(self):
        removecoordinates = []
        for coordinate in self.visibleCoordinates:
            x = coordinate[0]
            y = coordinate[1]
            obstacle = self.global_map[x][y]
            reachPoints = 0
            distancePoints = 0
            coordPoints = 0

            if (obstacle == '*') or (obstacle == '^') or (obstacle == '.'):
                removecoordinates.append([x,y])
                print('Removed: {} Reason: Wall or already went through'.format(coordinate))
                continue
            if obstacle == '~' and self.items['r'] < 1 and self.items['o'] < 1 and self.onLand:
                self.global_map_values[x][y] = -10000
                #print('Skipped water: [{} {}]'.format(x,y))
                continue
            
            withoutItemRoute = astarItems(self.AstarMap,self.position, [x,y], self.emptyitems, self.onRaft)
            
            if len(withoutItemRoute[0]):
                self.astar_memory[x][y] = withoutItemRoute
            else:
                self.astar_memory[x][y] = astarItems(self.AstarMap,self.position, [x,y], self.items, self.onRaft)

            if len(self.astar_memory[x][y][0]) > 0:
                if self.astar_memory[x][y][1]:
                    reachPoints = 10
                else:
                    reachPoints = 50
                    ## reduce points based on the distance
                distancePoints = (len(self.astar_memory[x][y][0])) * -0.2
                coordPoints = self.calculateCoordinatePoints([x,y])
                self.global_map_values[x][y] = reachPoints + distancePoints + coordPoints
                print('{},{} is worth {} points'.format(x,y, self.global_map_values[x][y]))
                #print('({},{}) ({}): pts = {}  reach = {}  dist = {}  coord = {} pathlength = {}'.format(x,y,self.global_map[x][y],self.global_map_values[x][y],reachPoints,distancePoints,coordPoints, len(self.astar_memory[x][y][0])))

            else:
                print('{},{} is not reachhable'.format(x,y))
                self.global_map_values[x][y] = -10000
            

            if (obstacle == ' ') and coordPoints < 2.5 and reachPoints > 1:
                print('Removed: {} Reason: not enough coordpoints ({})'.format(coordinate, coordPoints))
                removecoordinates.append([x,y])
                continue

            print('({},{}) ({}): pts = {}  reach = {}  dist = {}  coord = {} pathlength = {}'.format(x,y,self.global_map[x][y],self.global_map_values[x][y],reachPoints,distancePoints,coordPoints, len(self.astar_memory[x][y][0])))

        for coordinate in removecoordinates:
            
            self.visibleCoordinates.remove(coordinate)
            self.exploredCoordinates.append(coordinate)
            self.global_map_values[x][y] = -10000
        #print('Final Visible Coordinates: {}'.format(self.visibleCoordinates))
                
    ## Controller converts a list of positions into keyboard actions for the agent ##
    ## These actions are queued in actionQueue and pushed into the game one at a time ##
    def controller(self, positionList): ## Missing implementation for unlock and cut
        currentPos = self.position
        currentDir = self.direction

        if len(positionList) == 0:
            return

        if currentPos != positionList[0]:
            print("Error: Positions do not match {} -> {}". format(currentPos, positionList[0]))
            return

        for newPosition in positionList[1:]:
            movement = (newPosition[0] - currentPos[0], newPosition[1] - currentPos[1])
            if movement in self.rotationAngleTbl:
                newDirection = self.rotationAngleTbl[movement]
            else:
                print("Error: Invalid movement {} -> {} = {}".format(currentPos, newPosition,movement))
                return
            rotationRequired = (newDirection - currentDir) % 360
            if rotationRequired == 90:
                self.actionQueue.put('L')
            elif rotationRequired == 180:
                self.actionQueue.put('LL')
            elif rotationRequired == 270:
                self.actionQueue.put('R')

            if self.global_map[newPosition[0]][newPosition[1]] in self.requiredItems: #if tree or door then cut or unlock
                if self.global_map[newPosition[0]][newPosition[1]] == 'T':      
                    self.actionQueue.put('C')
                elif self.global_map[newPosition[0]][newPosition[1]] == '-':
                    self.actionQueue.put('U')

            self.actionQueue.put('F')
            currentPos = newPosition
            currentDir = newDirection
    
    def calculateCoordinatePoints(self, coordinate): # assigns points to each coordinate on the global map
        returnhomefunction = 0 ###replace later
        x = coordinate[0]
        y = coordinate[1]
        obstacle = self.global_map[x][y]

        if obstacle in ['k','a','o']:  #return 10 pts if new items collectable without losing items
            if self.onRaft:
                return 15
            else:
                return 30

        elif obstacle in ['T','-']: # returns 10 pts if agent contains pre-req to collect new items
            if obstacle == 'T' and self.items['a'] > 0:
                if self.onRaft:
                    return 40
                else:
                    return 30
            elif obstacle == '-' and self.items['k'] > 0:
                if self.onRaft:         # the agent prioritizes obtaining another raft over opening doors
                    return 15
                else:
                    return 30
            else:
                return 0

        elif obstacle == ' ': # values exploring land depending on whether agent is currently on a raft
            if self.onRaft:
                points = -5
            else:
                points = 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = self.global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if self.onRaft:
                                points += 0.1
                            else:
                                points += 0.5
            print('{} {}: points: {}'.format(x,y,points))
            return points
            #possible to shorten this... keep like this until confirmed

        elif obstacle == '~': # values exploring the water depending on whether agent is currently on a raft
            points = 0
            if (self.items['o'] < 1 and self.items['r'] < 1) and self.onRaft == 0:
                return 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = self.global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if self.onRaft:
                                points += 0.5
                            else:
                                points += 0.1
            return points
        elif obstacle == '$':
            if self.check_routehome(self.position, [x,y]):
                return 9999999
            return 0
        return 0


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
                        if [Iidx, Jidx] in self.placedStonesList:
                            self.global_map[Iidx][Jidx] = ' '
                        else:
                            self.global_map[Iidx][Jidx] = element
                elif (i == 2 and j == 2):
                    self.global_map[Iidx][Jidx] = '^'
                
                if [Iidx, Jidx] not in self.exploredCoordinates and [Iidx, Jidx] not in self.visibleCoordinates:
                    self.visibleCoordinates.append([Iidx, Jidx])
                     
            # else if the current viewmap reading is at the centre,
            # that is stored as agent directions.  


            self.AstarMap.updateGrid(self.global_map, self.onRaft)
  
    def move_agent(self, action):
        next_position = self.give_front_position(self.position)
        #print("{} ({}) next = {} : {}".format(self.position,self.direction, next_position, self.global_map[front_position[0]][front_position[1]]))

        if action == 'L' or action == 'l':
            self.direction = (self.direction + 90) % 360
        elif action == 'R' or action == 'r':
            self.direction = (self.direction - 90) % 360
        elif action == 'F' or action == 'f':
            
            if self.position not in self.exploredCoordinates:
                    self.exploredCoordinates.append(self.position)
            if self.position in self.visibleCoordinates:
                self.visibleCoordinates.remove(self.position)

            if self.global_map[next_position[0]][next_position[1]] not in self.blocks:
                prevElement = self.global_map[self.position[0]][self.position[1]]
                self.position = next_position
                nextElement = self.global_map[next_position[0]][next_position[1]]
                

                if nextElement in self.items:
                    self.items[nextElement] += 1
                
                #needs to be reviewed...
                if nextElement == '~':
                    if self.items['o'] > 0:
                        self.items['o'] -= 1
                        self.placedStonesList.append(next_position)

                    elif self.onLand: # Only change this if the previous position was land ' '
                        if self.items['r'] > 0:
                            self.items['r'] = self.items['r'] - 1
                            self.onRaft = 1
                            self.onLand = 0
                            print("on a raft")
                        else:
                            print("Error: no raft in inventory")

                    elif self.onRaft == 0:
                        print("Error: Raft not available")
                        
                elif nextElement == ' ':
                    self.onRaft = 0
                    self.onLand = 1
                    print("on land. ")


        elif (action == 'C' or action == 'c'):
            tree = self.global_map[next_position[0]][next_position[1]]
            if tree == 'T' and self.items['a'] > 0:
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

    def type_to_move(self):
        final_actions = ''
        while final_actions == '':
            input_actions = input("Type anything: ")
            for action in input_actions:
                final_actions = final_actions + action

        return final_actions

    def print_small_matrix(self, matrix, print_size):
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


    def print_large_matrix(self, matrix, print_size):
        print("\n+{}+".format("-" * print_size))
        for i in range(print_size):
            print('|', end = '')
            for j in range(print_size):
                    print(matrix[i][j], end = '')
            print('|')
        print("+{}+\n".format("-" * print_size))
        return 0


    def changeItems(self,totalItemUsed, totalNewItemCollected):
        for item in totalNewItemCollected:
            self.items[item] =+ 1
        for item in totalItemUsed:
            self.items[item] =- 1
        
            
    def main_loop(self):
        time.sleep(1)
        action_list = ['z']
        while (True):
            for i in range(len(action_list)):
                self.move_agent(action_list[i])
                self.view_window = self.TCP_Socket.recv_map()
                if len(self.view_window) > 0:
                    self.update_global_map()
                    self.print_small_matrix(self.view_window, self.view_size)
                    print("Item List: {}".format(self.items))
                        



            if self.actionQueue.empty():
                self.print_large_matrix(self.global_map, 160)
                self.update_global_map_values()
                print("Current Position: {}".format(self.position))
                print("Visible: {}".format(self.visibleCoordinates))
                print("Explored: {}".format(self.exploredCoordinates))
                print("Item List: {}".format(self.items))

                nextPosition = self.decideNextPosition()
                print("\nNext Position Chosen: {} ({})".format(nextPosition, self.global_map[nextPosition[0]][nextPosition[1]]))
                print("onLand: {} onRaft: {}".format(self.onLand, self.onRaft))

                #collect path from memory
                pathMemory = self.astar_memory[nextPosition[0]][nextPosition[1]]
                newPath = pathMemory[0]
                print("aStarMemory: {}".format(self.astar_memory[nextPosition[0]][nextPosition[1]]))
                self.controller(newPath)
                does_nothing = self.type_to_move()
            #Use this for manual human gameplay    
            #self.TCP_Socket.send_action(action_list)
            #self.maproute_testing = []

            #Use this for AI Keyboard Control
            
            if not self.actionQueue.empty():
                action_list = self.actionQueue.get()
                print(action_list)
                self.TCP_Socket.send_action(action_list)





# Input: python3 Agent -p [port_no]
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no, view_size)
new_agent.main_loop()

        



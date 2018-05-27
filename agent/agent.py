#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #

import sys
import pickle
import time
from queue import Queue
from rotation import rotate
from socketmanager import TCPSocketManager
from astar import astarItems, AstarMap
from yens import YenMultiPath
import copy

# agent class
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
        self.winmessage = 1
        self.deep_search_limit = 3


    # this function is to print the GlobalMap with Shrinked size
    # so it is easeir to debug
    def printMinimizedGlobalMap(self):
        
        colEdge = self.colEdge
        rowEdge = self.rowEdge


    def decideNextPosition(self):
        nextPosition = [80,80]
        points = -100000

        if self.items['$'] > 0:
            if self.decideRouteHome(self.position):
                return nextPosition

        for coordinate in self.visibleCoordinates:
            i = coordinate[0]
            j = coordinate[1]
            if self.global_map_values[i][j] > points:
                points = self.global_map_values[i][j]
                nextPosition = [i,j]
                #print('[{},{}] has higher points ({})'.format(i,j, self.global_map_values[i][j]))
            #else:
                #print('[{},{}] failed and has less points ({})'.format(i,j, self.global_map_values[i][j]))
        return nextPosition
        
    def checkRouteHome(self, startingpoint, treasurepoint):
        print("Trip to $ items: {}".format(self.items))
        firsttripresult = self.astarMinimum(self.AstarMap,startingpoint, treasurepoint, self.items, self.onRaft)
        print("First Trip to $: {}".format(firsttripresult))
        temp_globalmap_2 = self.global_map
        stonelocations = firsttripresult[4]
        remaining_items = firsttripresult[2]
        print('stones used for ($). Locations: {}'.format(stonelocations))
        for locations in stonelocations:
            temp_globalmap_2[locations[0]][locations[1]] = ' '
        temp_AstarMap = AstarMap(temp_globalmap_2)
        if len(firsttripresult[0]) > 0:
            hometripresult = self.astarMinimum(temp_AstarMap, treasurepoint, self.home, remaining_items, 0)
            print("Home Trip: {}".format(hometripresult))
        else:
            return 0
        if len(hometripresult[0]) > 0:
            return 1
    
    def decideRouteHome(self,startingpoint):
        astarresult = self.astarMinimum(self.AstarMap,startingpoint, self.home, self.items, 0)
        print('PathHome: {}'.format(astarresult))
        if len(astarresult[0]) > 0:
            if startingpoint == self.position:
                self.astar_memory[80][80] = astarresult
            return 1
        else:
            return 0
    
    def astarMinimum(self, AstarMap, position, goal, items, onRaft):
        stoneCount = items['o']
        starting_item_list = items.copy()

        for count in range(stoneCount+1):
            items = starting_item_list.copy()
            items['o'] = count
            items['r'] = 0
            testRoute = astarItems(AstarMap, position, goal, items, onRaft, [])
            print('testroute {} Length: {} stonecount {} items {} onRaft {}'.format(goal, len(testRoute[0]), count, items, onRaft))

            if (len(testRoute[0])) > 0:
                testRoute[2]['o'] = stoneCount - count
                if self.global_map[goal[0]][goal[1]] in self.items:
                    print('Target {} ({}) StonesUsed {} Route Length {} astar: {}'.format(goal, self.global_map[goal[0]][goal[1]],count, len(testRoute[0]), testRoute))
                return testRoute
        
        return astarItems(AstarMap, position, goal, starting_item_list, onRaft, [])
        
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
                self.global_map_values[x][y] = -10001
                #print('Skipped water: [{} {}]'.format(x,y))
                continue
            
            self.astar_memory[x][y] = self.astarMinimum(self.AstarMap,self.position, [x,y], self.items, self.onRaft)

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
                self.global_map_values[x][y] = -10002
            

            if (obstacle == ' ') and coordPoints < 2.5 and reachPoints > 1:
                print('Removed: {} Reason: not enough coordpoints ({})'.format(coordinate, coordPoints))
                removecoordinates.append([x,y])
                continue

            print('({},{}) ({}): pts = {}  reach = {}  dist = {}  coord = {} pathlength = {}'.format(x,y,self.global_map[x][y],self.global_map_values[x][y],reachPoints,distancePoints,coordPoints, len(self.astar_memory[x][y][0])))

        for coordinate in removecoordinates:
            
            self.visibleCoordinates.remove(coordinate)
            self.exploredCoordinates.append(coordinate)
            self.global_map_values[coordinate[0]][coordinate[1]] = -10003

    def calculate_globalMap_points(self, global_AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, search_level):
        removecoordinatesList = []
        
        #places a limit on deep search to prevent overload of computer processing power
        if search_level > self.deep_search_limit:
            return [AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, removecoordinatesList, 0]
        else:
            #Loop through all visible coordinate on the map and calculate points for each coordinate
            #Add up values of all coordinates that have value > 0
            for coordinate in self.visibleCoordinates:
                x, y = coordinate[0], coordinate[1]
                
                obstacle = global_map[x][y]
                
                if (obstacle == '*') or (obstacle == '^') or (obstacle == '.'):
                    global_map_values[x][y] = -10001
                    removecoordinatesList.append([x,y])
                    print('Removed: {} Reason: Wall or already went through'.format(coordinate))
                    continue
                elif obstacle == '~' and items['r'] < 1 and items['o'] < 1 and (onRaft == 0):
                    global_map_values[x][y] = -5000
                    continue
                
                temp_astar_memory = self.astarMinimum(global_AstarMap,position, [x,y], items, onRaft)
                placed_stone_list = temp_astar_memory[4]
                #placed_stone_list = []

                #astar returns [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable]
                #if stones are required placed then we need to which path is the best path based on global map points system
                
                
                if len(placed_stone_list) > 0 and obstacle in self.items:
                    print("{}: Stones used {}".format(coordinate, placed_stone_list))
                    print("{} ({}): astar returned: {}".format(coordinate, obstacle, temp_astar_memory))
                    temp_globalmap = copy.deepcopy(global_map)
                    temp_global_map_values = copy.deepcopy(global_map_values)
                    temp_astar_memory = copy.deepcopy(astar_memory)
                    print("\n\n ** DEEP SEARCH STARTING FOR {} ({}) from {} Layer {}\n\n".format(coordinate, obstacle, position, search_level))
                    multiStarRoutes = YenMultiPath(temp_globalmap, position, [x,y], items, onRaft)
                    max_points = 0
                    best_route = []

                    #Update maps for all multipleRoutes
                    for aStarRoute in multiStarRoutes:
                        temp_global_points = 0
                        new_items = aStarRoute[2]
                        new_raftstate = aStarRoute[3]
                        stone_locations = aStarRoute[4]

                        print("Updating a temp map with stones {}".format(stone_locations))
                        for location in stone_locations:
                            temp_globalmap[location[0]][location[1]] = ' '

                        temp_AstarMap = AstarMap(temp_globalmap)
                        
                        return_list = self.calculate_globalMap_points(temp_AstarMap, temp_globalmap, temp_global_map_values, temp_astar_memory, [x,y], new_items, new_raftstate, search_level + 1)
                        temp_global_points = return_list[8]
                        if temp_global_points > max_points:
                            max_points = temp_global_points
                            best_route = copy.deepcopy(aStarRoute)
                            print("\Better Path Found ({}) {} : {}\n".format(coordinate, temp_global_points, aStarRoute))
                        print("\nCurrent Path Points {} : {}\n".format(temp_global_points, aStarRoute[0]))
                        print("items after: {}".format(aStarRoute[2]))
                    print("\n\n ** DEEP SEARCH ENDING FOR {} ({}) from {} Layer {}\n\n".format(coordinate, obstacle, position, search_level))
                    print("Selected route for {} ({}) : {}".format(coordinate,obstacle, best_route))
                    astar_memory[x][y] = copy.deepcopy(best_route)

                else:
                    astar_memory[x][y] = temp_astar_memory.copy()

                totalPoints, remove_flag, reachPoints, distancePoints, coordPoints = self.calculateTotalCoordPoints(x,y, astar_memory[x][y], obstacle, global_map, onRaft, items, position)
                global_map_values[x][y] = totalPoints
                if remove_flag:
                    removecoordinatesList.append([x,y])
                if obstacle in self.items:
                    print('({},{}) ({}): pts = {}  reach = {}  dist = {}  coord = {} pathlength = {}'.format(x,y,obstacle,totalPoints,reachPoints,distancePoints,coordPoints, len(astar_memory[x][y][0])))

            totalMapPoints = self.calculate_TotalMapPoints(global_map_values, removecoordinatesList)

            return [global_AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, removecoordinatesList, totalMapPoints]
            
            ## loop through all coordinates and add points where > 0 for items only. 
            #print('Final Visible Coordinates: {}'.format(self.visibleCoordinates))
                    
    def calculate_TotalMapPoints(self, global_map_values, removecoordinatesList):
        totalMapPoints = 0
        for coordinate in self.visibleCoordinates:
            if coordinate not in removecoordinatesList:
                x, y = coordinate[0], coordinate[1]
                points = global_map_values[x][y]
                if points > 0:
                    totalMapPoints += points
        return totalMapPoints


    def calculateTotalCoordPoints(self, x, y, astar_memory, obstacle,global_map, onRaft, items, position):
        remove_flag = 0
        reachPoints, distancePoints, coordPoints = 0, 0, 0
        if len(astar_memory[0]) > 0:
            if astar_memory[1]:
                reachPoints = 10
            else:
                reachPoints = 50
            distancePoints = (len(astar_memory[0])) * -0.2   #reduce points based on distance
            coordPoints = self.calculateCoordPoints([x,y],global_map, onRaft, items, position)
            totalPoints = reachPoints + distancePoints + coordPoints
        else:
            #print('{},{} is not reachhable'.format(x,y))
            totalPoints = -10002

        if (obstacle == ' ') and coordPoints < 2.5 and reachPoints > 1:
            #print('Removed: {} Reason: not enough coordpoints ({})'.format([x,y], coordPoints))
            remove_flag = 1
                
        return totalPoints, remove_flag, reachPoints, distancePoints, coordPoints


    def calculateCoordPoints(self, coordinate, global_map, onRaft, items, position): # assigns points to each coordinate on the global map
        returnhomefunction = 0 ###replace later
        x = coordinate[0]
        y = coordinate[1]
        obstacle = global_map[x][y]

        if obstacle in ['k','a','o']:  #return 10 pts if new items collectable without losing items
            if onRaft:
                return 15
            else:
                return 100

        elif obstacle in ['T','-']: # returns 10 pts if agent contains pre-req to collect new items
            if obstacle == 'T' and self.items['a'] > 0:
                if onRaft:
                    return 200
                else:
                    return 90
            elif obstacle == '-' and self.items['k'] > 0:
                if onRaft:         # the agent prioritizes obtaining another raft over opening doors
                    return 30
                else:
                    return 100
            else:
                return 0

        elif obstacle == ' ': # values exploring land depending on whether agent is currently on a raft
            if onRaft:
                points = -5
            else:
                points = 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = self.global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if onRaft:
                                points += 0.1
                            else:
                                points += 0.5
            return points
            #possible to shorten this... keep like this until confirmed

        elif obstacle == '~': # values exploring the water depending on whether agent is currently on a raft
            points = 0
            if (items['o'] < 1 and items['r'] < 1) and onRaft == 0:
                return 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if onRaft:
                                points += 0.5
                            else:
                                points += 0.1
            return points
        elif obstacle == '$':
            if self.checkRouteHome(position, [x,y]):
                return 999999999
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

    ## agentController converts a list of positions into keyboard actions for the agent ##
    ## These actions are queued in actionQueue and pushed into the game one at a time ##
    def agentController(self, positionList): ## Missing implementation for unlock and cut
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
    
    ## move_agent takes the AI actions and updates the agent's status on the saved global map. 

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
                self.update_masterGlobalMap_values()
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
                self.agentController(newPath)
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

        



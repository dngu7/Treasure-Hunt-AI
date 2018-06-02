#---------------------------------------------------------------------------------------------------------------------------------------------------#
# COMP 3411/9414 Artificial Intelligence
# Project 3 (Option 1): Treasure Hunt
# Group 37
# David Nguyen (z5154591)
# Yong Yooshin (z3461805)

#---------------------------------------------------------------------------------------------------------------------------------------------------#
#  Agent Description Summary                                                                                                                        
#  The agent uses the following algorithms and AI techniques to find the treasure and return home.                                                  
#   
#  Name                                      Description
#  1. Top Global Map Memory                  > Stores local map obstacles into global map
#  2. Object Score System                    > Calculates Scores for each obstacle on the global map to decide next move.  
#  3. A-Star Heuristic Search                > Generates the shortest path using the least number of items
#  4. Yens-Astar Multiple Path Search        > Generates multiple paths using various stone placement combinations
#  5. Decision Trees with pruning            > Assessment of multiple paths using future global map states using object Score system (deep search)
#  6. Deep Global Map Scores Memory          > Stores deep searched global map Scores to avoid repeitive decision trees

#---------------------------------------------------------------------------------------------------------------------------------------------------#
#  Agent Design: 
#                               
# When the agent starts, it begins the main loop function which carries out 5 important steps. The agent stores the map received from the game
# in a large 160x160 global map (global_map_obstacles) using the update_global_map_obstacles() function. Next, each coordinate in the map is assigned Scores 
# based on a system which prioritizes exploration of land/water and picks up items depending on 3 factors: Reachability, item importance and
# distance. These Scores are calculated after every move (using the calculateTotalCoordPoints function) and is saved in the top_global_map_points. 
# The agent uses these Scores to determine the next move using decideNextPosition() function. 
# With the new position selected, the agent uses a combination of A-Star, Yen's Algorithm and a decision tree to determine the best route to take.
# The route is fed into the agentController function which converts a list of positions into player commands that are sent to the game socket. 

# The coordinate with the highest Scores is chosen and multiple routes are created using a combination A-Star Search and Yen's Algorithm.
# The agent decides between different routes by calculating the total Scores of future global map states Scores. It carries this out by generating 
# temporary maps with the new stone placements and generates paths to all visible items using path search described above. 
# This process continues to deepen the decision tree and explores all possible outcomes until all items are unreachable. 
# The path that generates the highest Scores based on its future states are returned and executed by the agent. 
# Memory and pruning have also been implemented to optimize the decision tree calculation speed. As the agent generates future global map states, it saves
# its values in memory (deep_global_map_points) to avoid repeitive calculations in the future. When a path is found from the agent's current position 
# to the treasure and then home, then the agent executes the entire "final" path immediately. This "final path" pruning saves the agent significant 
# time as it only needs to calculate the final winning path once. 


#---------------------------------------------------------------------------------------------------------------------------------------------------#

import sys
import pickle
import time
import copy

from queue import Queue
from rotation import rotate
from socketmanager import TCPSocketManager
from astar import astarItems, AstarMap, manhattan
from yens import YenAstarMultiPath

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Agent Class Object
# Contains functions required to find the treasure and return home                                                                              
#---------------------------------------------------------------------------------------------------------------------------------------------------#
class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.global_map_size = 160
        self.global_map_obstacles = [['?'] * self.global_map_size for i in range(self.global_map_size)]
        self.global_map_distance = [[0] * self.global_map_size for i in range(self.global_map_size)]
        self.top_global_map_points = [[0] * self.global_map_size for i in range(self.global_map_size)]
        self.deep_global_map_points = [[{}] * self.global_map_size for i in range(self.global_map_size)]
        self.AstarGlobalMap = AstarMap(self.global_map_obstacles)
        self.items = {'k' : 0, 'o' : 0, 'a' : 0, 'r' : 0, '$' : 0}
        self.visibleItemsPts = {'k' : 100, 'o' : 100, 'a' : 100, 'T' : 100, '$' : 10000}
        self.direction = 0
        self.position = [80,80]
        self.home = [80,80]
        self.onRaft = 0
        self.onLand = 1
        self.actionQueue = Queue()
        self.rotationAngleTbl = {(-1,0): 0, (0,-1): 90, (1,0): 180, (0,1): 270}
        self.placedStonesCoordinates = []
        self.visibleCoordinates = []
        self.visibleItems = []
        self.exploredCoordinates = [[80,80]]
        self.deep_search_limit = 20
        self.max_layer_points = [0] * (self.deep_search_limit + 1)
        self.update_global_values_flag = 1
        self.theFinalPath = []

    #------------------------------------------------------------------------------------#
    # checkDeepMapValues()
    # This function checks if future global map state Scores have already been calculated 
    #  and saved in self.deep_global_map_points 
    #------------------------------------------------------------------------------------#
    def checkDeepMapValues(self, start, goal, stoneLocation, currentItems):
        x = start[0]
        y = start[1]

        goal = str(goal)
        stoneLocation = str(stoneLocation)
        currentItems = str(currentItems)

        if goal in self.deep_global_map_points[x][y]:
            if stoneLocation in self.deep_global_map_points[x][y][goal]:
                if currentItems in self.deep_global_map_points[x][y][goal][stoneLocation]:
                    deepMapValue = self.deep_global_map_points[x][y][goal][stoneLocation][currentItems]
                    return deepMapValue
        return 0

    #------------------------------------------------------------------------------------#
    # addDeepMapValues()
    # This function adds future global map state Scores to self.deep_global_map_points 
    #  in order to avoid repeitive calculations. 
    #------------------------------------------------------------------------------------#           
    def addDeepMapValues(self, start, goal, stoneLocation, currentItems, deepMapValue):
        x = start[0]
        y = start[1]
        goal = str(goal)
        stoneLocation = str(stoneLocation)
        currentItems = str(currentItems)

        if deepMapValue == 0:
            deepMapValue = 1

        if goal not in self.deep_global_map_points[x][y]:
            self.deep_global_map_points[x][y][goal] = {}
        if stoneLocation not in self.deep_global_map_points[x][y][goal]:
            self.deep_global_map_points[x][y][goal][stoneLocation] = {}
        self.deep_global_map_points[x][y][goal][stoneLocation][currentItems] = deepMapValue

    #------------------------------------------------------------------------------------#
    # decideNextPosition()
    # This function returns the next position for the agent by finding visible coordinate with the highest Scores stored
    # If the agent holds the treasure and a route home is feasible, then it immediately goes to [80,80]
    #------------------------------------------------------------------------------------#                
    def decideNextPosition(self):
        nextPositions = [[80,80]]
        maxpoints = -1000
        maxcoordPoint = -1000
        goal_list = []
        

        # If agent holds the treasure, then it searches for a path home. 
        if self.items['$'] > 0:
            if self.decideRouteHomefromTreasure(self.position):
                return nextPositions
        # Loops through all possible coordinates and choose the coordinate with the highest Scores. 
        for coordinate in self.visibleCoordinates:
            i = coordinate[0]
            j = coordinate[1]
            coordPoints = self.top_global_map_points[i][j]
            distancePoints = self.global_map_distance[i][j] * 0.1
            totalPoints = coordPoints - distancePoints
            obstacle = self.global_map_obstacles[i][j]
            if totalPoints > maxpoints:
                maxpoints = totalPoints
                nextPositions = [[i,j]]
                nextObstacle = obstacle
                maxcoordPoint = coordPoints
            elif maxcoordPoint == coordPoints and nextObstacle in self.visibleItemsPts and nextObstacle == obstacle:
                nextPositions.append([i,j])

        return nextPositions
    
    #------------------------------------------------------------------------------------#
    # decideRouteHomefromTreasure()
    # This function checks if there is a path home from the current starting position
    #------------------------------------------------------------------------------------#
    def decideRouteHomefromTreasure(self,starting_coordinate):
        astarresult = self.astarMinimum(self.AstarGlobalMap,starting_coordinate, self.home, self.items, 0)
        if len(astarresult[0]) > 0:
            return 1
        return 0     
    #------------------------------------------------------------------------------------#
    # checkRouteHome()
    # This function checks if there is a path home from the current starting position
    #------------------------------------------------------------------------------------#
    def checkRouteHome(self, starting_coordinate, treasure_coordinate):
        # Calculates the route to the treasure using the starting and treasure coordinates
        routeToTreasure = self.astarMinimum(self.AstarGlobalMap,starting_coordinate, treasure_coordinate, self.items, self.onRaft)
        # Generates list of remaining items and stone used during the routetoTreasure
        remaining_items, stone_coordinates = routeToTreasure[2],routeToTreasure[4] 
        # Updates a temporary globalmap with the stones used during the routetoTreasure
        temp_globalmap_2 = copy.deepcopy(self.global_map_obstacles)
        temp_AstarMap = AstarMap(temp_globalmap_2)
        for coordinates in stone_coordinates:
            temp_globalmap_2[coordinates[0]][coordinates[1]] = ' '

        # If route to treasure exists then the agent determines if there is a route from the treasure to home. 
        if len(routeToTreasure[0]) > 0:
            routeHome = self.astarMinimum(temp_AstarMap, treasure_coordinate, self.home, remaining_items, 0)
        else:
            return 0
        # If route home from treasure exists then execute this path
        if len(routeHome[0]) > 0:
            return 1
    
    #------------------------------------------------------------------------------------#
    # astarMinimum()
    # Generates a path using AStar Search with the least number of stones possible. 
    # This function prioritizes usage of the stones over the raft.
    #------------------------------------------------------------------------------------#
    def astarMinimum(self, AstarMap, position, goal, items, onRaft):
        totalStoneCount = items['o']
        starting_item_list = items.copy()
        starting_stones = 0
        # Priortize the raft
        if items['r'] > 0:
            starting_stones = totalStoneCount
        
        for count in range(starting_stones, totalStoneCount+1):
            items = starting_item_list.copy()
            items['o'] = count
            
            testRoute = astarItems(AstarMap, position, goal, items, onRaft,[])

            if (len(testRoute[0])) > 0:
                testRoute[2]['o'] = totalStoneCount - count
                return testRoute
        
        return astarItems(AstarMap, position, goal, starting_item_list, onRaft, [])

    #------------------------------------------------------------------------------------#
    # decideBestRoute()
    # This function creates the best route to a goal(coordinate) using a modified 
    # yen algorithm/astar heuristic search and a decision tree.
    #------------------------------------------------------------------------------------#
    def decideBestRoute(self, goal_list):
        #self.max_layer_points = [0] * (self.deep_search_limit + 1)
        best_goal_points = 0
        best_goal_route = []
        for goal in goal_list:
            #Generates a simple path using Astar Search
            astar_memory = self.astarMinimum(self.AstarGlobalMap, self.position, goal, self.items, self.onRaft)
            bestRoute, bestRouteStones = astar_memory[0], astar_memory[4]
            obstacle = self.global_map_obstacles[goal[0]][goal[1]]

            # If the goal is water or land, then immediately return the simple astar path. 
            if not ((obstacle in self.items and len(bestRouteStones) > 0) or (obstacle == 'o' and len(bestRoute) > 0 and self.items['o'] > 0)):
                return bestRoute

            print("Agent is calculating the best route to {} ({}). Please wait...".format(goal, obstacle))
            

            #Generates multiple paths using a hybrid Yen-Astar Search Algorithm. 
            aStarMultiPath_List = YenAstarMultiPath(self.global_map_obstacles, self.position, goal, self.items, self.onRaft)  #Generate Multiple Paths

            #Setup copies of the global maps to use in generating the decision tree
            starting_globalmap = copy.deepcopy(self.global_map_obstacles)
            starting_visibleItems = self.visibleItems.copy()
            max_deepMapPoints = 0

            # Loop through all routes to decide the best route to take using future global map states
            for routeNb, someRoute in enumerate(aStarMultiPath_List):
                print("Agent is exploring future global map states of this route. Please wait... \n {}".format(someRoute[0]))
                temp_globalmap = copy.deepcopy(starting_globalmap)
                temp_visibleItems = starting_visibleItems.copy()
                temp_visibleItems.remove(goal)
                search_level = 0

                new_items = someRoute[2]
                new_raftstate = someRoute[3]
                new_stone_coordinates = self.placedStonesCoordinates + someRoute[4]

                # Agent checks if this route's future global map state has been assessed previously. 
                globalMapPoints = self.checkDeepMapValues(self.position, goal, new_stone_coordinates, self.items)

                #If the route's global map state hasn't been found, then generate a temporary map with the new stone locations created on the new route. 
                if globalMapPoints == 0:
                    for i in new_stone_coordinates:
                        temp_globalmap[i[0]][i[1]] = ' '
                    temp_AstarMap = AstarMap(temp_globalmap)
            
                    #Calculate the value of the route's future global map state if the route was executed
                    globalMapPoints = self.deepSearch_globalMapPoints(temp_AstarMap, temp_globalmap, temp_visibleItems, goal, new_items, new_raftstate, search_level, new_stone_coordinates)
                    if globalMapPoints < 0:
                        continue
                    #Store the value of the route's future global map state 
                    self.addDeepMapValues(self.position, goal, new_stone_coordinates, self.items, globalMapPoints)
                    

                #The best route will have the highest global map Scores. This path is saved. 
                if globalMapPoints > max_deepMapPoints:
                    max_deepMapPoints = globalMapPoints
                    bestRoute = someRoute[0].copy()
                    bestRouteStones = new_stone_coordinates.copy()
                    
                    #The winning path was found so the entire search is stopped and this path is prioritized
                    if max_deepMapPoints > 100000:
                        self.theFinalPath = bestRoute + self.theFinalPath
                        break

            if len(self.theFinalPath) > 0:
                return self.theFinalPath

            if globalMapPoints >= best_goal_points:
                best_goal_points = globalMapPoints
                best_goal_route = bestRoute.copy()
        return best_goal_route

    #------------------------------------------------------------------------------------#
    # deepSearch_globalMapPoints
    # This function calculates the total global map Scores of a position using future states 
    # based on all possible routes takeen to all visible coordinates 
    #------------------------------------------------------------------------------------#
    def deepSearch_globalMapPoints(self, DS_AstarMap, globalmap, visibleItems, start, items, raftstate, search_level, new_stone_coordinates):
        
        # Limits the level of deep search to avoid long calculation times. 
        search_level = search_level + 1
         # if search level exceeded, just return 0 as a value.
        if search_level > self.deep_search_limit: return 0

        # Setup Variables
        current_globalMapPoints = 0
        bestRouteStones = []
        bestRoute = []
        best_astar_path = []
        new_stone_coordinates_prev = new_stone_coordinates.copy()

        # Loops through all visible items and adds the total coordinate Scores for each. 
        for goal in visibleItems:
            max_deepMapPoints = 0
            obstacle = globalmap[goal[0]][goal[1]]

            #Build shortest path
            curr_astar_path = self.astarMinimum(DS_AstarMap, start, goal, items, raftstate)
            currRoute, currRouteStones = curr_astar_path[0], curr_astar_path[4]
            
            #If no path possible then ignore
            if len(currRoute) == 0: continue

            #If stones used, then it requires multiple path assessment to determine best possible path
            if (obstacle in self.items and len(currRouteStones) > 0) or (obstacle == 'o' and len(currRoute) > 0): #if stones are used then ai needs to begin planning by generating multiple options with YenAstarMultiPath

             
                #Multiple Paths will be generated using YenAStar 
                aStarMultiPath_List = YenAstarMultiPath(globalmap, start, goal, items, raftstate)

                #Save globalmap and visible items. These change each route based on stone coordinates. 
                starting_globalmap = copy.deepcopy(globalmap)
                starting_visibleItems = visibleItems.copy()

                #Remove destimation from visible_items temporarily
                if goal in starting_visibleItems: starting_visibleItems.remove(goal)

                #Begin loop through each new path generated by the YenAStar
                for routeNb, someRoute in enumerate(aStarMultiPath_List):
                    
                    #Setup Variables for someRoute (Someroute is the current route being assessed using a Score system)
                    new_items, new_raftstate, new_stone_coordinates = someRoute[2], someRoute[3], someRoute[4]
                    globalMapPoints = 0

                    #create a new map and visible items list
                    temp_globalmap = copy.deepcopy(starting_globalmap)
                    temp_visibleItems = starting_visibleItems.copy()

                    #update stone coordinates of the new map based on new stones generated by this route
                    new_stone_coordinates = new_stone_coordinates_prev + new_stone_coordinates

                               
                    # Agent checks if this route's future global map state has been assessed previously. 
                    globalMapPoints = self.checkDeepMapValues(start, goal, new_stone_coordinates, items)

                    if globalMapPoints == 0:
                        #build new map with new updated stone coordinates
                        for i in new_stone_coordinates:
                            temp_globalmap[i[0]][i[1]] = ' '
                        temp_AstarMap = AstarMap(temp_globalmap)

                        #Calculate map Scores as if this route was excuted by the agent
                        #Begins deepsearch to determine best route based on the new map states. 
                        globalMapPoints = self.deepSearch_globalMapPoints(temp_AstarMap, temp_globalmap, starting_visibleItems, goal, new_items, new_raftstate, search_level, new_stone_coordinates)                 
                        if globalMapPoints < 0:
                            return -10000
                        #Store the value of the route's future global map state 
                        self.addDeepMapValues(start, goal, new_stone_coordinates, items, globalMapPoints)

                    #Compares map Scores to best route. Saves if new route provides better future state Scores.  
                    if globalMapPoints >= max_deepMapPoints:
                        max_deepMapPoints = globalMapPoints
                        bestRoute = copy.deepcopy(someRoute[0])
                        bestRouteStones = new_stone_coordinates.copy()

                        #End the search if the final path to the treasure and home is found. 
                        if globalMapPoints > 100000:
                            self.theFinalPath = bestRoute[1:] + self.theFinalPath
                            return globalMapPoints
                                          
            else:
                bestRoute = currRoute.copy()
                bestRouteStones = currRouteStones.copy()

            #Scores system for Treasure->Home Path Detection. 
            if obstacle == '$':
                temp_DS_map = AstarMap(globalmap)
                homesearch = self.astarMinimum(temp_DS_map, goal, [80,80], items, 0)
                
                if len(homesearch[0]) > 0:
                    self.theFinalPath = bestRoute[1:]
                    return 10000000000000
            
            current_globalMapPoints += max_deepMapPoints + self.visibleItemsPts[obstacle]
 

            
        return current_globalMapPoints  


    def updateDistance(self):
        for coordinate in self.visibleCoordinates:
            self.global_map_distance[coordinate[0]][coordinate[1]] = int(manhattan(self.position, coordinate))

    #------------------------------------------------------------------------------------#
    # update_top_global_points
    # Updates the top_global_map_points memory for all visible and unexplored coordinates
    #------------------------------------------------------------------------------------#
    def update_top_global_points(self):
        
        removecoordinatesList = []
        
        # Calculate the Scores for visible coordinates only
        for coordinate in self.visibleCoordinates:
            x, y = coordinate[0], coordinate[1]
            obstacle = self.global_map_obstacles[x][y] 

            # Only update items periodically to avoid excessive calculations
            if self.update_global_values_flag == 0 and obstacle in self.items:
                continue
            
            # Water is given negative Scores if the agent has no raft, no stones and is not on a raft
            if obstacle == '~' and self.items['r'] < 1 and self.items['o'] < 1 and (self.onRaft == 0):
                self.top_global_map_points[x][y] = -500000000
                continue
            
            # astar path is generated from the agents current position to the coordinate
            astar_memory = self.astarMinimum(self.AstarGlobalMap, self.position, [x,y], self.items, self.onRaft)
            placed_stone_list = astar_memory[4]

            # These are sent to the the calculateTotalCoord Function below. 
            totalPoints, remove_flag, reachPoints, coordPoints = self.calculateTotalCoordPoints(x, y, astar_memory, self.global_map_obstacles, self.onRaft, self.items, self.position)

            # Save Scores for the coordinate
            self.top_global_map_points[x][y] = totalPoints

            if remove_flag:
                removecoordinatesList.append([x,y])

        #remove coordinate from visible list if deemed by the calculateTotalCoordPoints function
        for coordinate in removecoordinatesList: 
            self.visibleCoordinates.remove(coordinate)
            self.exploredCoordinates.append(coordinate)
            self.top_global_map_points[coordinate[0]][coordinate[1]] = -10003
        self.update_global_values_flag = 0

    #------------------------------------------------------------------------------------#
    # calculateTotalCoordPoints: Calculates the TOTAL Scores for a coordinate 
    #  
    # All coordinates are assigned Scores based on its reachability (reachPoints) and importance to the agent (coordPoints)
    # Reachability is determine using whether astar search can generate a path with/without any items.
    # Coordinates that do not require items are higher in value/priority 
    # Importance to the agent is calculated in the calculateCoordPoints() function below. 
    #------------------------------------------------------------------------------------#
    
    def calculateTotalCoordPoints(self, x, y, astar_memory, global_map, onRaft, items, position):
        remove_flag = 0
        obstacle = global_map[x][y]
        reachPoints, coordPoints = 0, 0

        #Door, agent and boundaries are ignored
        if (obstacle == '*') or (obstacle == '^') or (obstacle == '.'):
            return 0,1,0,0
        
        #reachPoints depedent on two factors: Reachable with/without items. 
        if len(astar_memory[0]) > 0: #Path of length zero means coordinate is not reachable
            if astar_memory[1]: #if list is empty, then it requires no items. This gives it 50 Scores. 
                reachPoints = 10
            else:
                reachPoints = 50
            coordPoints = self.calculateCoordPoints([x,y],global_map, onRaft, items, position) #Calculates coordinate Scores using function
            totalPoints = reachPoints + coordPoints
        else:
            #print('{},{} is not reachable'.format(x,y))
            totalPoints = -10002

        #Land ignored if it doesnt exceed threshold
        if (obstacle == ' ') and coordPoints < 2.6 and reachPoints > 1:
            #print('Removed: {} Reason: not enough coordpoints ({})'.format([x,y], coordPoints))
            remove_flag = 1
            totalPoints = 0
                
        return totalPoints, remove_flag, reachPoints, coordPoints

    #------------------------------------------------------------------------------------#
    # calculateCoordPoints: Calculates the coordinate Scores for a given coordinate 
    #  
    # Below is the Score setup for each coordinate type (land, water, item)
    #------------------------------------------------------------------------------------#
    
    def calculateCoordPoints(self, coordinate, global_map, onRaft, items, position): # assigns Scores to each coordinate on the global map
        x = coordinate[0]
        y = coordinate[1]
        obstacle = global_map[x][y]

        #Scores setup for key, axe and stone. Varies whether agent is on a raft or on land
        if obstacle in ['k','a','o']:  #return 10 pts if new items collectable without losing items
            if onRaft:
                return 8
            else:
                return 20
        #Scores setup for Tree and Door. Dependant on whether agent has axe or key 
        elif obstacle in ['T','-']: # returns 10 pts if agent contains pre-req to collect new items
            if obstacle == 'T' and self.items['a'] > 0:
                if onRaft:
                    return 8
                else:
                    return 20
            elif obstacle == '-' and self.items['k'] > 0:
                if onRaft:         # the agent prioritizes obtaining another raft over opening doors
                    return 8
                else:
                    return 20
            else:
                return 0
        #Scores setup for land. Dependent on surrounding unknown space (?), water and raft state  
        elif obstacle == ' ': # values exploring land depending on whether agent is currently on a raft
            if onRaft:
                Scores = -5
            else:
                Scores = 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = self.global_map_obstacles[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if onRaft:
                                Scores += 0.2
                            else:
                                Scores += 1
                        if surrounding_obstacle == '~':
                            Scores += 0.2
            return Scores
        #Scores setup for water. Dependent on surrounding unknown space (?), water and current items/raft
        elif obstacle == '~': # values exploring the water depending on whether agent is currently on a raft
            Scores = 0
            if (items['o'] < 1 and items['r'] < 1) and onRaft == 0:
                return 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if onRaft:
                                Scores += 1.5
                            else:
                                Scores += 0.5
            return Scores
        #Scores setup for treasure. Agent only goes for treasure if it can plot a path home
        elif obstacle == '$':
            if self.checkRouteHome(position, [x,y]):
                return 999999999
            return -10000
        return 0

    #------------------------------------------------------------------------------------#
    # update_global_map_obstacles()
    #  Updates the global_map_obstacles using the map received from the TCP Socket
    #------------------------------------------------------------------------------------#
    
    def update_global_map_obstacles(self):
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
                        if [Iidx, Jidx] in self.placedStonesCoordinates:
                            self.global_map_obstacles[Iidx][Jidx] = ' '
                        else:
                            self.global_map_obstacles[Iidx][Jidx] = element
                elif (i == 2 and j == 2):
                    self.global_map_obstacles[Iidx][Jidx] = '^'
                    self.top_global_map_points[Iidx][Jidx] = -10000

                    if [Iidx, Jidx] not in self.exploredCoordinates:
                        self.exploredCoordinates.append([Iidx, Jidx])
                    if [Iidx, Jidx] in self.visibleCoordinates:
                        self.visibleCoordinates.remove([Iidx, Jidx])
                    if [Iidx, Jidx] in self.visibleItems:
                        self.visibleItems.remove([Iidx,Jidx])
                
                if [Iidx, Jidx] not in self.exploredCoordinates and [Iidx, Jidx] not in self.visibleCoordinates:
                    if self.global_map_obstacles[Iidx][Jidx] in self.visibleItemsPts:
                        self.visibleItems.append([Iidx,Jidx])

                    astar_path = self.astarMinimum(self.AstarGlobalMap,self.position, [Iidx, Jidx], self.items, self.onRaft)
                    totalPoints, remove_flag, reachPoints, coordPoints = self.calculateTotalCoordPoints(Iidx, Jidx, astar_path, self.global_map_obstacles, self.onRaft, self.items, self.position)

                    if remove_flag:
                        self.top_global_map_points[Iidx][Jidx] = 0
                        self.exploredCoordinates.append([Iidx, Jidx])
                        remove_flag = 0
                    else:
                        self.top_global_map_points[Iidx][Jidx] = totalPoints
                        self.visibleCoordinates.append([Iidx, Jidx])
                
            self.AstarGlobalMap.updateGrid(self.global_map_obstacles, self.onRaft)

    #------------------------------------------------------------------------------------#
    # agentController: 
    # Converts a list of positions into keyboard actions for the agent 
    # These actions are queued in actionQueue and pushed into the game one at a time 
    #------------------------------------------------------------------------------------#
    def agentController(self, positionList): ## Missing implementation for unlock and cut
        requiredItems = {'-' : 'k', 'T' : 'a'}
        currentPos = self.position
        currentDir = self.direction

        if len(positionList) == 0:
            return

        if currentPos != positionList[0]:
            #print("Error: Positions do not match {} -> {}". format(currentPos, positionList[0]))
            return

        for newPosition in positionList[1:]:
            movement = (newPosition[0] - currentPos[0], newPosition[1] - currentPos[1])
            if movement in self.rotationAngleTbl:
                newDirection = self.rotationAngleTbl[movement]
            else:
                #print("Error: Invalid movement {} -> {} = {}".format(currentPos, newPosition,movement))
                return
            rotationRequired = (newDirection - currentDir) % 360
            if rotationRequired == 90:
                self.actionQueue.put('L')
            elif rotationRequired == 180:
                self.actionQueue.put('LL')
            elif rotationRequired == 270:
                self.actionQueue.put('R')

            if self.global_map_obstacles[newPosition[0]][newPosition[1]] in requiredItems: #if tree or door then cut or unlock
                if self.global_map_obstacles[newPosition[0]][newPosition[1]] == 'T':      
                    self.actionQueue.put('C')
                elif self.global_map_obstacles[newPosition[0]][newPosition[1]] == '-':
                    self.actionQueue.put('U')

            self.actionQueue.put('F')
            currentPos = newPosition
            currentDir = newDirection
    
    #------------------------------------------------------------------------------------#
    # move_agent: 
    # Takes the actions and updates the agent's position and direction to ensure it 
    # aligns with the current game
    #------------------------------------------------------------------------------------#
    def move_agent(self, action):
        blocks = ['T','*','-','.']
        next_position = self.give_front_position(self.position)

        if action == 'L' or action == 'l':
            self.direction = (self.direction + 90) % 360
        elif action == 'R' or action == 'r':
            self.direction = (self.direction - 90) % 360
        elif action == 'F' or action == 'f':
            
            if self.position not in self.exploredCoordinates:
                self.exploredCoordinates.append(self.position)
            if self.position in self.visibleCoordinates:
                self.visibleCoordinates.remove(self.position)

            if self.global_map_obstacles[next_position[0]][next_position[1]] not in blocks:
                prevElement = self.global_map_obstacles[self.position[0]][self.position[1]]
                self.position = next_position
                nextElement = self.global_map_obstacles[next_position[0]][next_position[1]]
            
                if nextElement in self.items:
                    self.items[nextElement] += 1
                    self.update_global_values_flag = 1
                
                if nextElement == '~':
                    if self.items['o'] > 0:
                        self.items['o'] -= 1
                        self.placedStonesCoordinates.append(next_position)
                        self.update_global_values_flag = 1

                    elif self.onLand: # Only change this if the previous position was land ' '
                        if self.items['r'] > 0:
                            self.items['r'] = self.items['r'] - 1
                            self.onRaft = 1
                            self.onLand = 0
                            #print("on a raft")
                            self.update_global_values_flag = 1

                    #elif self.onRaft == 0:
                    #    print("Error: Raft not available")
                        
                elif nextElement == ' ':
                    if self.onRaft:
                        self.update_global_values_flag = 1
                    self.onRaft = 0
                    self.onLand = 1
                    
        elif (action == 'C' or action == 'c'):
            tree = self.global_map_obstacles[next_position[0]][next_position[1]]
            if tree == 'T' and self.items['a'] > 0:
                self.items['r'] += 1
                self.update_global_values_flag = 1
            

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

    def checkWinCondition(self, start_time):
        if self.items['$'] > 0 and self.position == self.home:
            print("Winner Winner Chicken Dinner!")
            end_time = time.time() - start_time
            print("Time: {}".format(end_time))
            sys.exit()
                 
    def main_loop(self):
        time.sleep(1)
        start_time = time.time()
        refreshvalues_flag = 0
        action_list = ['z']
        while (True):

            for i in range(len(action_list)):                                               
                self.move_agent(action_list[i])                 # Moves agent in current program to ensure allignment with the game
                self.checkWinCondition(start_time)              # Ends game if win conditions met (Treasure found and returned home)
                self.view_window = self.TCP_Socket.recv_map()   # Receives map from socket and saves it
                if len(self.view_window) > 0:                
                    self.update_global_map_obstacles()
                    self.print_small_matrix(self.view_window, self.view_size)

            if self.actionQueue.empty():                       
                refreshvalues_flag += 1
                #self.print_large_matrix(self.global_map_obstacles, 160)

                self.updateDistance()
                if self.update_global_values_flag or refreshvalues_flag > 1:   # Update coordinate values every 2 moves. Immediate update is required during certain conditions
                    self.update_top_global_points()
                    refreshvalues_flag = 0


                nextPosition = self.decideNextPosition()                       
                bestRoute = self.decideBestRoute(nextPosition)

                self.agentController(bestRoute)                         #Converts route into game actions. Game actions are added into the actionQueue
            
            if not self.actionQueue.empty():
                action_list = self.actionQueue.get()
                #print(action_list)
                self.TCP_Socket.send_action(action_list)


# Input: python3 agent.py -p [port_no]
port_no = int(sys.argv[2])
ip_address = '127.0.0.1'
view_size = 5


new_agent = Agent(ip_address, port_no, view_size)
new_agent.main_loop()

        



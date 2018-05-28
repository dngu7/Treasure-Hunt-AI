#           Sample Agent for Text-Based Adventure Game      #
#           Implemented in Python3.6                        #

import sys
import pickle
import time
from queue import Queue
from rotation import rotate
from socketmanager import TCPSocketManager
from astar import astarItems, AstarMap, manhattan
from yens import YenAstarMultiPath
import copy


class Agent:
    def __init__(self, ip_address, port_no, view_size):
        self.TCP_Socket = TCPSocketManager(ip_address, port_no, view_size)
        
        self.view_size = view_size
        self.view_window = [[' '] * view_size for i in range(view_size)]
        self.global_map_size = 160
        self.global_map = [['?'] * self.global_map_size for i in range(self.global_map_size)]
        self.global_map_values = [[0] * self.global_map_size for i in range(self.global_map_size)]
        self.global_map_distance = [[0] * self.global_map_size for i in range(self.global_map_size)]
        self.astar_memory = [[[],[],[]] * self.global_map_size for i in range(self.global_map_size)]
        self.items = {'k' : 0, 'o' : 0, 'a' : 0, 'r' : 0, '$' : 0}
        self.visibleItemsPts = {'k' : 100, 'o' : 100, 'a' : 100, 'T' : 100, '$' : 10000}
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
        self.AstarGlobalMap = AstarMap(self.global_map)
        self.visibleCoordinates = []
        self.visibleItems = []
        self.exploredCoordinates = [[80,80]]


        self.deep_search_limit = 6
        self.update_global_values_flag = 0


    # this function is to print the GlobalMap with Shrinked size
    # so it is easeir to debug
    def printMinimizedGlobalMap(self):
        
        colEdge = self.colEdge
        rowEdge = self.rowEdge


    def decideNextPosition(self):
        nextPosition = [80,80]
        maxpoints = -100000

        if self.items['$'] > 0:
            if self.decideRouteHome(self.position):
                return nextPosition

        for coordinate in self.visibleCoordinates:
            i = coordinate[0]
            j = coordinate[1]
            normalvalue = self.global_map_values[i][j]
            distancevalue = self.global_map_distance[i][j] * 0.1
            coordPoints = normalvalue - distancevalue
            #print("{} ({}): {} = {} - {}".format(coordinate, self.global_map[i][j], coordPoints, normalvalue, distancevalue))
            if coordPoints > maxpoints:
                maxpoints = coordPoints
                nextPosition = [i,j]

        return nextPosition
        
    def checkRouteHome(self, startingpoint, treasurepoint):
        print("Trip to ($) | Starting  items: {}".format(self.items))
        firsttripresult = self.astarMinimum(self.AstarGlobalMap,startingpoint, treasurepoint, self.items, self.onRaft)
        print("First Trip to $: {}".format(firsttripresult))
        temp_globalmap_2 = self.global_map
        stonelocations = firsttripresult[4]
        remaining_items = firsttripresult[2]
        print('Stones used for first trip($). StoneLocations: {}'.format(stonelocations))
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
        astarresult = self.astarMinimum(self.AstarGlobalMap,startingpoint, self.home, self.items, 0)
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
            
            testRoute = astarItems(AstarMap, position, goal, items, onRaft,[])

            if (len(testRoute[0])) > 0:
                testRoute[2]['o'] = stoneCount - count
                if self.global_map[goal[0]][goal[1]] in self.items:
                    print('From {} Target {} ({}) StonesUsed {} Route Length {} astar: {}'.format(position, goal, self.global_map[goal[0]][goal[1]],count, len(testRoute[0]), testRoute))
                return testRoute
        
        return astarItems(AstarMap, position, goal, starting_item_list, onRaft, [])

    def update_global_values(self):
        self.update_global_values_flag = 0
        removecoordinatesList = []
        for coordinate in self.visibleCoordinates:
            x, y = coordinate[0], coordinate[1]
            obstacle = self.global_map[x][y] 

            if obstacle == '~' and self.items['r'] < 1 and self.items['o'] < 1 and (self.onRaft == 0):
                self.global_map_values[x][y] = -5000
                continue

            astar_memory = self.astarMinimum(self.AstarGlobalMap, self.position, [x,y], self.items, self.onRaft)
            placed_stone_list = astar_memory[4]
            totalPoints, remove_flag, reachPoints, coordPoints = self.calculateTotalCoordPoints(x, y, astar_memory, self.global_map, self.onRaft, self.items, self.position)

            self.global_map_values[x][y] = totalPoints

            if remove_flag:
                removecoordinatesList.append([x,y])

        for coordinate in removecoordinatesList: 
            self.visibleCoordinates.remove(coordinate)
            self.exploredCoordinates.append(coordinate)
            self.global_map_values[coordinate[0]][coordinate[1]] = -10003
                
    def decideBestRoute(self, goal):
        astar_memory = self.astarMinimum(self.AstarGlobalMap, self.position, goal, self.items, self.onRaft)
        bestRoute = astar_memory[0]
        bestRouteStones = astar_memory[4]
        obstacle = self.global_map[goal[0]][goal[1]]

        #goal is not an item 
        #goal requires no rocks

        if not ((obstacle in self.items and len(bestRouteStones) > 0) or (obstacle == 'o' and len(bestRoute) > 0 and self.items['o'] > 0)):
            return bestRoute

        print("\n0 Start {} | Goal {} ({})| Original Path {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], bestRoute))
        print("0 Start {} | Goal {} ({})| Stones Required {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], bestRouteStones))
        print("0 Start {} | Goal {} ({})| Visible Items {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], self.visibleItems))

        aStarMultiPath_List = YenAstarMultiPath(self.global_map, self.position, goal, self.items, self.onRaft)
        starting_globalmap = copy.deepcopy(self.global_map)
        starting_visibleItems = self.visibleItems.copy()
        max_points = 0

        for someRoute in aStarMultiPath_List:
            temp_globalmap = copy.deepcopy(starting_globalmap)
            temp_visibleItems = starting_visibleItems.copy()
            temp_visibleItems.remove(goal)
            search_level = 0

            new_items = someRoute[2]
            new_raftstate = someRoute[3]
            new_stone_locations = someRoute[4]

            for i in new_stone_locations:
                temp_globalmap[i[0]][i[1]] = ' '


            temp_AstarMap = AstarMap(temp_globalmap)

            
            globalMapPoints = self.deepSearch_globalMapPoints(temp_AstarMap, temp_globalmap, temp_visibleItems, goal, new_items, new_raftstate, search_level)

            print("0 Start {} | Goal {} ({})| Potential Path {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], someRoute[0]))
            print("0 Start {} | Goal {} ({})| Potential Map Points {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], globalMapPoints))
                    
            if globalMapPoints > max_points:
                max_points = globalMapPoints
                bestRoute = someRoute[0].copy()
                bestRouteStones = new_stone_locations.copy()
                print("0 Start {} | Goal {} ({})| New Best Path {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], bestRoute))
                print("0 Start {} | Goal {} ({})| Stones Used {}".format(self.position, goal, self.global_map[goal[0]][goal[1]], bestRouteStones))
                print("0 Start {} | Goal {} ({})| New Best Points {}\n".format(self.position, goal, self.global_map[goal[0]][goal[1]], max_points))

        return bestRoute

    def deepSearch_globalMapPoints(self, DS_AstarMap, globalmap, visibleItems, start, items, raftstate, search_level):
        current_globalMapPoints = 0
        search_level = search_level + 1
        if search_level > self.deep_search_limit:
            return 0
        # Loop through visible coordinates
        
        print("\n{} Start {} ({}) | visibleItems {}".format(search_level, start, globalmap[start[0]][start[1]], visibleItems))
        for goal in visibleItems:
            best_astar_path = self.astarMinimum(DS_AstarMap, start, goal, items, raftstate)
            bestRouteStones = best_astar_path[4]
            bestRoute = best_astar_path[0]
            max_points = 0
            obstacle = globalmap[goal[0]][goal[1]]
            


            if (obstacle in self.items and len(bestRouteStones) > 0) or (obstacle == 'o' and len(bestRoute) > 0): #if stones are used then ai needs to begin planning by generating multiple options with YenAstarMultiPath

                print("\n{} Start {} | Goal {} ({})| Original Path {}".format(search_level, start, goal, globalmap[goal[0]][goal[1]], best_astar_path[0]))
                print("{} Start {} | Goal {} ({})| Stones Required {}".format(search_level, start, goal, globalmap[goal[0]][goal[1]], bestRouteStones))

                aStarMultiPath_List = YenAstarMultiPath(globalmap, start, goal, items, raftstate)
                starting_globalmap = copy.deepcopy(globalmap)
                starting_visibleItems = visibleItems.copy()
                

                for someRoute in aStarMultiPath_List:
                    temp_globalmap = copy.deepcopy(starting_globalmap)
                    temp_visibleItems = starting_visibleItems.copy()
                    if goal in starting_visibleItems:
                        starting_visibleItems.remove(goal)
                    search_level = 0

                    new_items = someRoute[2]
                    new_raftstate = someRoute[3]
                    new_stone_locations = someRoute[4]

                    for i in new_stone_locations:
                        temp_globalmap[i[0]][i[1]] = ' '


                    temp_AstarMap = AstarMap(temp_globalmap)

                    globalMapPoints = self.deepSearch_globalMapPoints(temp_AstarMap, temp_globalmap, starting_visibleItems, goal, new_items, new_raftstate, search_level)                 
                    print("{} Start {} | Goal {} ({})| Potential Path {}".format(search_level, start, goal, temp_globalmap[goal[0]][goal[1]], someRoute[0]))
                    print("{} Start {} | Goal {} ({})| Map Points {}".format(search_level, start, goal, temp_globalmap[goal[0]][goal[1]], globalMapPoints))
                    print("{} Start {} | Goal {} ({})| Finishing items {}".format(search_level, start, goal, temp_globalmap[goal[0]][goal[1]], someRoute[2]))

                    if globalMapPoints > max_points:
                        max_points = globalMapPoints
                        best_astar_path = someRoute.copy()
                        bestRoute = someRoute[0].copy()
                        bestRouteStones = new_stone_locations.copy()
                        print("{} Start {} | Goal {} ({})| Best Path {}".format(search_level, start, goal, globalmap[goal[0]][goal[1]], bestRoute))
                        print("{} Start {} | Goal {} ({})| Stones Used {}".format(search_level, start, goal, globalmap[goal[0]][goal[1]], bestRouteStones))
                        print("{} Start {} | Goal {} ({})| Best Points {}\n".format(search_level, start, goal, globalmap[goal[0]][goal[1]], max_points))

                if len(bestRoute) > 0:
                    if obstacle == '$':
                        print("Final run Item: {}".format(best_astar_path[2]))
                        homesearch = self.astarMinimum(DS_AstarMap, goal, [80,80], best_astar_path[2], 0)
                        if len(homesearch[0]) > 0:
                            print("Found Path to Treasure and Home.")
                            return 10000000000000
                    current_globalMapPoints += max_points + self.visibleItemsPts[obstacle]

        return current_globalMapPoints    

        # refresh all points in the temporary global map values because tehre are now new stones and new items

        #if stones are used to reach an object then you must loop using deepSearch to determine which route you should use 
        

    def refreshDistance(self):
        for coordinate in self.visibleCoordinates:
            self.global_map_distance[coordinate[0]][coordinate[1]] = int(manhattan(self.position, coordinate))

    def update_masterGlobalMap_values(self):
        new_values = self.calculate_globalMap_points(self.visibleCoordinates, self.AstarGlobalMap, self.global_map, self.global_map_values, self.astar_memory, self.position, self.items, self.onRaft,0)
        self.AstarGlobalMap = new_values[0]
        self.global_map = new_values[1].copy()
        self.global_map_values = new_values[2].copy()
        self.astar_memory = new_values[3].copy()
        self.position = new_values[4]
        self.items = new_values[5]
        self.onRaft = new_values[6]
        removecoordinatesList = new_values[7]
        map_points = new_values[8]

        for coordinate in removecoordinatesList: 
            self.visibleCoordinates.remove(coordinate)
            self.exploredCoordinates.append(coordinate)
            self.global_map_values[coordinate[0]][coordinate[1]] = -10003

    def calculate_globalMap_points(self, visibleCoordinates, global_AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, search_level):
        removecoordinatesList = []
        
        #places a limit on deep search to prevent overload of computer processing power
        if search_level > self.deep_search_limit:
            return [AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, removecoordinatesList, 0]
        else:
            #Loop through all visible coordinate on the map and calculate points for each coordinate
            #Add up values of all coordinates that have value > 0
            for coordinate in visibleCoordinates:
                x, y = coordinate[0], coordinate[1]
                obstacle = global_map[x][y]
                
                if obstacle == '~' and items['r'] < 1 and items['o'] < 1 and (onRaft == 0):
                    global_map_values[x][y] = -5000
                    continue
                
                temp_astar_memory = self.astarMinimum(global_AstarMap,position, [x,y], items, onRaft)
                placed_stone_list = temp_astar_memory[4]
                #placed_stone_list = []

                #astar returns [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable]
                #if stones are required placed then we need to which path is the best path based on global map points system
                
                
                if (len(placed_stone_list) > 0 and obstacle in self.items) or (obstacle == 'o' and len(temp_astar_memory[0]) > 0):
                    print("{}: Stones used {}".format(coordinate, placed_stone_list))
                    print("{} ({}): astar returned: {}".format(coordinate, obstacle, temp_astar_memory))
                    temp_globalmap = copy.deepcopy(global_map)
                    temp_global_map_values = copy.deepcopy(global_map_values)
                    temp_astar_memory_copy = copy.deepcopy(astar_memory)
                    print("\n\n ** DEEP SEARCH STARTING FOR {} ({}) from {} Layer {}\n\n".format(coordinate, obstacle, position, search_level))
                    t0 = time.time()

                    aStarMultiPath_storage = YenAstarMultiPath(temp_globalmap, position, [x,y], items, onRaft)
                    max_points = 0

                    t1 = time.time()

                    #Update maps for all multipleRoutes
                    for aStarRoute in aStarMultiPath_storage:
                        t3 = time.time()
                        temp_globalmap_copy = copy.deepcopy(temp_globalmap)
                        temp_visibleCoordinates = visibleCoordinates.copy() #visisble coordinates are new... 
                        temp_global_points = 0
                        new_items = aStarRoute[2]
                        new_raftstate = aStarRoute[3]
                        new_stone_locations = aStarRoute[4]
                        temp_visibleCoordinates.remove(coordinate)
                        

                        print("TESTING potential route ({}) {}".format(coordinate, aStarRoute[0]))
                        #print("before: global map without stones")
                        #self.print_large_matrix(temp_globalmap_copy, 160)
                        for location in new_stone_locations:
                            temp_globalmap_copy[location[0]][location[1]] = ' '
                        print("after: global map with stones {}".format(new_stone_locations))
                        self.print_large_matrix(temp_globalmap_copy, 160)

                        temp_AstarMap = AstarMap(temp_globalmap_copy)
                        print("Starting next layer search for {} ({}) to determine global points".format(coordinate, obstacle))
                        return_list = self.calculate_globalMap_points(temp_visibleCoordinates, temp_AstarMap, temp_globalmap_copy, temp_global_map_values, temp_astar_memory_copy, [x,y], new_items, new_raftstate, search_level + 1)
                        temp_global_points += return_list[8]
                        print("Total global points ({}): {}".format(coordinate, temp_global_points))

                        if temp_global_points > max_points:
                            max_points = temp_global_points
                            astar_memory[x][y] = copy.deepcopy(aStarRoute)
                            print("++BETTER Path Found ({}) {} : {}".format(coordinate, temp_global_points, aStarRoute))
                        else:
                            print("--Worse Path Path Found {} : {}".format(temp_global_points, aStarRoute[0]))
                        print("Items after path finished: {}\n".format(aStarRoute[2]))
                    t2 = time.time()
                    print("\n\n ** DEEP SEARCH ENDING FOR {} ({}) from {} Layer {}".format(coordinate, obstacle, position, search_level))
                    print("Selected route for {} ({}) from {}: {}\n\n".format(coordinate,obstacle, position, astar_memory[x][y]))
                    print("YenASTarMultiPath Time = {}".format(t1-t0))
                    print("One Path Route Choice DeepSearch Time = {}".format(t2-t3))
                    print("Total Path Route Choice DeepSearch Time = {}".format(t2-t1))

                else:
                    astar_memory[x][y] = temp_astar_memory.copy()

                totalPoints, remove_flag, reachPoints, coordPoints = self.calculateTotalCoordPoints(x,y, astar_memory[x][y], global_map, onRaft, items, position)
                global_map_values[x][y] = totalPoints
                if remove_flag:
                    removecoordinatesList.append([x,y])
                if obstacle in self.items:
                    print('({},{}) ({}): pts = {}  reach = {}  dist = {}  coord = {} pathlength = {}'.format(x,y,obstacle,totalPoints,reachPoints,coordPoints, len(astar_memory[x][y][0])))

            totalMapPoints = self.calculate_TotalMapPoints(global_map_values, removecoordinatesList)
            print("totalMapPoints FOR position {}: {}\n\n".format(position, totalMapPoints))

            return [global_AstarMap, global_map, global_map_values, astar_memory, position, items, onRaft, removecoordinatesList, totalMapPoints]
            
            ## loop through all coordinates and add points where > 0 for items only. 
            #print('Final Visible Coordinates: {}'.format(self.visibleCoordinates))
                    
    def calculate_TotalMapPoints(self, global_map_values, removecoordinatesList):
        totalMapPoints = 0
        print("\n--Calculating Map Points--")
        for coordinate in self.visibleCoordinates:
            if coordinate not in removecoordinatesList:
                x, y = coordinate[0], coordinate[1]
                points = global_map_values[x][y]
                if points > 0:
                    totalMapPoints += points
                    print("{} ({}): +{}".format(coordinate, self.global_map[coordinate[0]][coordinate[1]],points))
        print("--Final Map Points = {}--\n".format(totalMapPoints))
        return totalMapPoints


    def calculateTotalCoordPoints(self, x, y, astar_memory, global_map, onRaft, items, position):
        remove_flag = 0
        obstacle = global_map[x][y]
        reachPoints, coordPoints = 0, 0

        if (obstacle == '*') or (obstacle == '^') or (obstacle == '.'):
            return 0,1,0,0
            
        if len(astar_memory[0]) > 0:
            if astar_memory[1]:
                reachPoints = 10
            else:
                reachPoints = 50
            coordPoints = self.calculateCoordPoints([x,y],global_map, onRaft, items, position)
            totalPoints = reachPoints + coordPoints
        else:
            #print('{},{} is not reachhable'.format(x,y))
            totalPoints = -10002

        if (obstacle == ' ') and coordPoints < 2.5 and reachPoints > 1:
            #print('Removed: {} Reason: not enough coordpoints ({})'.format([x,y], coordPoints))
            remove_flag = 1
            totalPoints = 0
                
        return totalPoints, remove_flag, reachPoints, coordPoints


    def calculateCoordPoints(self, coordinate, global_map, onRaft, items, position): # assigns points to each coordinate on the global map
        returnhomefunction = 0 ###replace later
        x = coordinate[0]
        y = coordinate[1]
        obstacle = global_map[x][y]

        if obstacle in ['k','a','o']:  #return 10 pts if new items collectable without losing items
            if onRaft:
                return 8
            else:
                return 20

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
                                points += 0.2
                            else:
                                points += 0.5
                        if surrounding_obstacle == '~':
                            points += 0.3
            return points
            #possible to shorten this... keep like this until confirmed

        elif obstacle == '~': # values exploring the water depending on whether agent is currently on a raft
            points = 0
            if (items['o'] < 2 and items['r'] < 1) and onRaft == 0:
                return 0
            for x_1 in range(-2,3):
                for y_2 in range(-2,3):
                    if (x + x_1 in range(self.global_map_size)) and (y + y_2 in range(self.global_map_size)):
                        surrounding_obstacle = global_map[x + x_1][y + y_2]
                        if surrounding_obstacle == '?':
                            if onRaft:
                                points += 1.5
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
                    self.global_map_values[Iidx][Jidx] = -10000

                    if [Iidx, Jidx] not in self.exploredCoordinates:
                        self.exploredCoordinates.append([Iidx, Jidx])
                    if [Iidx, Jidx] in self.visibleCoordinates:
                        self.visibleCoordinates.remove([Iidx, Jidx])
                    if [Iidx, Jidx] in self.visibleItems:
                        self.visibleItems.remove([Iidx,Jidx])
                
                if [Iidx, Jidx] not in self.exploredCoordinates and [Iidx, Jidx] not in self.visibleCoordinates:
                    if self.global_map[Iidx][Jidx] in self.visibleItemsPts:
                        self.visibleItems.append([Iidx,Jidx])

                    astar_path = self.astarMinimum(self.AstarGlobalMap,self.position, [Iidx, Jidx], self.items, self.onRaft)
                    totalPoints, remove_flag, reachPoints, coordPoints = self.calculateTotalCoordPoints(Iidx, Jidx, astar_path, self.global_map, self.onRaft, self.items, self.position)

                    if remove_flag:
                        self.global_map_values[Iidx][Jidx] = 0
                        self.exploredCoordinates.append([Iidx, Jidx])
                        remove_flag = 0
                    else:
                        self.global_map_values[Iidx][Jidx] = totalPoints
                        self.visibleCoordinates.append([Iidx, Jidx])
                
                
                     
            # else if the current viewmap reading is at the centre,
            # that is stored as agent directions.  


            self.AstarGlobalMap.updateGrid(self.global_map, self.onRaft)

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
                    self.update_global_values_flag = 1
                
                #needs to be reviewed...
                if nextElement == '~':
                    if self.items['o'] > 0:
                        self.items['o'] -= 1
                        self.placedStonesList.append(next_position)
                        self.update_global_values_flag = 1

                    elif self.onLand: # Only change this if the previous position was land ' '
                        if self.items['r'] > 0:
                            self.items['r'] = self.items['r'] - 1
                            self.onRaft = 1
                            self.onLand = 0
                            print("on a raft")
                            self.update_global_values_flag = 1
                        else:
                            print("Error: no raft in inventory")

                    elif self.onRaft == 0:
                        print("Error: Raft not available")
                        
                elif nextElement == ' ':
                    if self.onRaft:
                        self.update_global_values_flag = 1
                    self.onRaft = 0
                    self.onLand = 1
                    
                


        elif (action == 'C' or action == 'c'):
            tree = self.global_map[next_position[0]][next_position[1]]
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
        refreshvalues_flag = 0
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
                refreshvalues_flag += 1
                self.print_large_matrix(self.global_map, 160)
                self.refreshDistance()
                if self.update_global_values_flag or refreshvalues_flag > 1:
                    self.update_global_values()
                    refreshvalues_flag = 0

                print("Current Position: {}".format(self.position))
                print("Visible: {}".format(self.visibleCoordinates))
                
                print("Explored: {}".format(self.exploredCoordinates))
                print("Item List: {}".format(self.items))
                print("\nVisibleitems: ")
                for i in self.visibleItems:
                    print("{} ({}) ({})".format(i, self.global_map[i[0]][i[1]], self.global_map_values[i[0]][i[1]]))

                nextPosition = self.decideNextPosition()
                bestRoute = self.decideBestRoute(nextPosition)
                print("\nNext Position Chosen: {} ({}) ({})".format(nextPosition, self.global_map[nextPosition[0]][nextPosition[1]], self.global_map_values[nextPosition[0]][nextPosition[1]]))
                print("onLand: {} onRaft: {}".format(self.onLand, self.onRaft))

                #collect path from memory
                #pathMemory = self.astar_memory[nextPosition[0]][nextPosition[1]]
                #newPath = pathMemory[0]
                #print("aStarMemory: {}".format(self.astar_memory[nextPosition[0]][nextPosition[1]]))
                self.agentController(bestRoute)
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

        




#!/usr/bin/python3.6

from pqueue import PriorityQueue

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Acknowledgement
# Resource: https://raw.githubusercontent.com/ichinaski/astar/master/astar.py
# - resource used are: graph, astar and node class
#---------------------------------------------------------------------------------------------------------------------------------------------------#


#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Graph Class Object
# Contains functions required to find the children of if positions were given.
# It also gives the heuristic value for current position if goal was given. 
#---------------------------------------------------------------------------------------------------------------------------------------------------#
class Graph:
    """
    Abstract graph.
    Inherit from this class and implement its methods to have a working Graph
    """
    def getChildren(self, position):
        pass

    def getHCost(self, position, goal):
        '''
        Heuristic value of a certain node. For a dijkstra implementation, return always 0
        '''
        pass

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# manhattan
# function to return manhattan heuristics
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def manhattan(start, goal):
    x1,y1 = start
    x2,y2 = goal
    
    return abs(x1 - x2) + abs(y1 - y2)


#---------------------------------------------------------------------------------------------------------------------------------------------------#
# AstarMap(Graph): Class Object
# Inherits Graph class to suit our global agent map.
#---------------------------------------------------------------------------------------------------------------------------------------------------#
  
class AstarMap(Graph):
    
    requiredItems = {'-' : 'k', 'T' : 'a'}
    
    def __init__(self, grid, agentState = 0):
        self.grid = grid
        if len(grid) >= len(grid[0]):
            self.size = len(grid)
        else:
            self.size = len(grid[0])
        self.agentState = agentState

    #---------------------------------------------------#
    # updateGrid
    # create nodes connections.
    #---------------------------------------------------#
    def updateGrid(self, newGrid, agentState = []):
        self.grid = newGrid
        self.agentState = agentState
        
    #---------------------------------------------------#
    # updateState
    # updating states such as on raft state
    #---------------------------------------------------#  
    def updateState(self, newState):
        self.agentState = newState 

    #---------------------------------------------------#
    # getRaftState
    # get raft state
    #---------------------------------------------------# 
    def getRaftState(self):
        return self.agentState

    #---------------------------------------------------#
    # getHCost
    # calculate manhattan and return
    #---------------------------------------------------#     
    def getHCost(self, start, goal):
        hcost = manhattan(start,goal)
        return hcost
    
    #---------------------------------------------------#
    # getChildren
    # Get all legal children at current point
    # getChildren() will return the lists contatining:
    # [d, cost, item, element]
    #
    # where: 
    # d - the position index in grid
    #   - d[0] represents row while d[1] represents column
    # cost - the cost to get on to the current position to the neighbour one
    #      - will be always 1.
    # item - gives what sort of items it needs in order to get to the neighbour one
    # element - what sort of gird element it was in current child.
    #---------------------------------------------------#
    def getChildren(self, point, itemAvailable, currRaftState, parentStonePlace):
        y,x = point
    
        # find all indices that is neibour to current point
        neighbours = []
        for i,j in [ [-1, 0], [1, 0], [0, -1], [0, 1] ]:
            
            currI = y + i
            currJ = x + j
            if currI >= 0 and currI < self.size  and currJ >= 0 and  currJ < self.size:
                neighbours.append( [currI, currJ] )

        # find all legal neighbours
        legalNeighbours = []
        for direction in neighbours:
            
            # if crossing to one of neibbour is legal,
            # add on to the legalNeighbours lists
            if self.checkLegalState(direction, itemAvailable, currRaftState, parentStonePlace ):
                element = self.grid[direction[0]][direction[1]]
                itemRequired = self.getItemRequired(direction, itemAvailable, currRaftState)
                cost2Cross = 1 # assuming cost to go to next index is always one.

                # increase the cost to 20 if rocks or raft were used to cross.
                if itemRequired and (itemRequired == 'o' or itemRequired == 'r') :
                    cost2Cross = 20
                legalNeighbours.append( [direction, cost2Cross, itemRequired, element] )
                  
        return legalNeighbours

    #---------------------------------------------------#
    # getItemRequired
    # This function what sort of items were required to 
    # get to current directions of child.
    #---------------------------------------------------#
    def getItemRequired(self, d, itemAvailable, raftState):
    
        element = self.grid[d[0]][d[1]]
        itemlists = {'k', 'o', 'a', 'r', '$'}

        #self.requiredItems s=  {'-' : 'k', 'T' : 'a'}
        # if current map has the element which is on requiredItems 
        # lists, we just simply return that
        if element in self.requiredItems:
            return self.requiredItems[element] 
            
        # else if we have special case with water as element,
        # we have following option:
        # 1) if we are on raft, we do not require any item
        # 2) if we are not on raft but still have stone
        #    in itemAvailable, we will return stone
        # 3) if we have gained raft item we return raft.
        # Note: stone has higher priority to use then using raft.
        elif element == '~' and itemAvailable:
            if raftState:
                return {}
            elif 'o' in itemAvailable and itemAvailable['o'] >= 1:
                return 'o'
            elif 'r' in itemAvailable and itemAvailable['r'] >= 1:
                return 'r'
        else:
            return []
    #---------------------------------------------------# 
    # getItemCollected
    # return the item when it needs to collect
    # by consequence of getting there
    #---------------------------------------------------#
    def getItemCollected(self, d):
        
        element = self.grid[d[0]][d[1]]
        itemlists = {'k', 'o', 'a','$'}
        if element in itemlists:
            return element
            
        elif element == 'T':
            return 'r'
        return {}

    #---------------------------------------------------#
    # getRaftState
    # get current node's raft state.
    #---------------------------------------------------#
    def getRaftState(self):
        return self.agentState

    #---------------------------------------------------#
    # checkLegalState
    # this function will return true or false
    # for the check whether it has legal path 
    # for the a_star algorithm
    #---------------------------------------------------#
    def checkLegalState(self, d,items, currRaftState, parentStonePlace):

        raftState = currRaftState
        element = self.grid[d[0]][d[1]]
        
        obstacles = ['~', 'T', '-', '*', '?','.']

        # if we are already on the raft or 
        # have items to cross water
        if (element  == '~' and (raftState == 1 or ('r' in items and items['r'] > 0) 
                                    or ('o' in items and items['o'] > 0 ) 
                                    or (d in parentStonePlace)
                                     ) ):

            return 1
            
        # if we have key and door is the neighbour
        elif (element == '-' and 'k' in items and items['k'] > 0 ):
            return 1
        # if we have axe to cut down the tree and not on the raft
        elif (element == 'T' and 'a' in items and items['a'] > 0 
                and raftState == 0):
            return 1

        # if the neighbour is not obstacles
        elif (element not in obstacles ):
            return 1
        
        # Otherwise illegal
        else:
          return 0

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Node: Class Object
# Inherits Graph class to suit our global agent map.
#---------------------------------------------------------------------------------------------------------------------------------------------------#
class Node:
    def __init__(self, position, cost=0, parent=None):
        # State representation. It can be a tuple, an integer, 
        # or any data structure that holds your current state for this node
        self.position = position
        self.cost = cost
        self.parent = parent
        
#---------------------------------------------------------------------------------------------------------------------------------------------------#
# PathNode(Node):: Class Object
#
# This class will implement Node class but specific to our problem.
# Each node (called "PathNode") will store:
#     (a) Item remaining so far.
#     (b) Cost to getting to that node
#     (c) Raft State at that node
#     (d) Stone placed so far.
#---------------------------------------------------------------------------------------------------------------------------------------------------#
class PathNode(Node):
    def __init__(self, position, itemAvailable = {}, cost = 0, parent=None, raftState = 0):
    
        Node.__init__(self, position, cost, parent)
        self.raftState = raftState
        self.itemAvailable = itemAvailable
        self.newItemsCollected = {}
        self.stoneLocations = []
        #self.element = element

    #---------------------------------------------------#
    # getItemsCollectedSofar
    # This will return what item it has collected during
    # the path of astar.
    #---------------------------------------------------#   
    def getItemsCollectedSofar(self):
        return self.newItemsCollected
    
    #---------------------------------------------------#
    # setItemCollected
    # Set the dictionary of item collected.
    #---------------------------------------------------#
    def setItemCollected(self, itemCollectedList):
        self.newItemsCollected = itemCollectedList.copy()

    #---------------------------------------------------#
    # addNewItems2Collected
    # Add new item that is collected to Item list.
    #---------------------------------------------------#    
    def addNewItems2Collected(self, newItem):
        if newItem in self.newItemsCollected:
            self.newItemsCollected[newItem] += 1
        else:
            self.newItemsCollected[newItem] = 1

    #---------------------------------------------------#
    # getItemAvailable
    # give item remained in current node.
    #---------------------------------------------------#   
    def getItemAvailable(self):
        return self.itemAvailable
    
    #---------------------------------------------------#
    # getRaftState
    # return raft state for current node
    #---------------------------------------------------#
    def getRaftState(self):
        return self.raftState

    #---------------------------------------------------#
    # setRaftState
    # setter for new raft state.
    #---------------------------------------------------#
    def setRaftState(self, raftState):
        self.raftState = raftState

    #---------------------------------------------------#
    # getStonePlaced
    # getter for the list of positions where the stone was placed.
    #---------------------------------------------------#
    def getStonePlaced(self):
        return self.stoneLocations

    #---------------------------------------------------#
    # addStonePlaced
    # add on the new stone coordinate to the list of stone placed positions.
    #---------------------------------------------------#
    def addStonePlaced(self, stoneCoord):
        self.stoneLocations += stoneCoord


#---------------------------------------------------------------------------------------------------------------------------------------------------#
# astarItems
#
# This is similar to usual astar but Nodes are now having
# items or raft State to record. 
# The previous PathNode description tells in detail how it stores.
#
# Input:
# - This function has inputs as following:
#     - [graph, start, goal, itemsAvailable, initialRaftState, illegalEdges]
#     - graph: The graph which uses AstarGraph class.
#     - start: starting position as the list not tuple.
#     - goal: goal position which is also list.
#     - itemsAvailable: dictionary which contains the items as the key and stores the counter
#     - initialRaftState: whether current agent is on the raft or not.
#     - illegalEdges: options for the user to say the path is illegal.
#
# Output: 
# - This function will return following:
#     - [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace]
#     - path: path generated by astar which contains lists of positions.
#         eg. [[1,2], [1,3]]
#     - itemUsedState: this is to tell whether any items during the path.
#     - finalItemList: item dictionary after it has reached to the goal.
#     - finalStonePlace: the position list which contains the position of stones
#                        which was placed to the water to cross.
#---------------------------------------------------------------------------------------------------------------------------------------------------#

def astarItems(graph, start, goal, itemsAvailable, initialRaftState, illegalEdges):
    
    # Fringe. Nodes not visited yet
    openList = PriorityQueue()

    # Visited Nodes. Each one will store it's parent position
    closedList = {}


    # assign some start and goal points
    # and push start point as a node to openList.
    start_tuple = tuple(start)
    goal_tuple = tuple(goal)
    node = PathNode(start_tuple, itemsAvailable.copy())
    node.setRaftState(initialRaftState)
    openList.push(node)

    
    while openList:
        
        # if openList does not contain any node
        # we will break.     
        curr_node, _ = openList.pop()    
        if not curr_node:
            break
        
        position, cost = curr_node.position, curr_node.cost

        if position in closedList:
            # Oops. Already expanded.
            continue

        # Save the node in the closed list, and keep track of its parent
        if curr_node.parent != None:
            closedList[position] = curr_node.parent.position
        else:   
            closedList[position] = curr_node.position
        
        # arrived to goal so save it as goal node.
        if position == goal_tuple:
            goalNode = curr_node
            break
            
        # copy some parent properties
        curr_available = curr_node.getItemAvailable()
        raftState = curr_node.getRaftState()
        parentStonePlace = curr_node.getStonePlaced().copy()
        
        # for each legal child for current parent,
        for childPosition, actionCost, itemRequired, element in graph.getChildren(position, curr_available, 
                                                                                  raftState,parentStonePlace):
            copyStonePlaced = parentStonePlace.copy()

            # if illegal edges were given 
            # and current one is illegal, ignore current child.
            pos1 = list(position).copy()
            pos2 = childPosition
            if illegalEdges and ([pos1, pos2] == illegalEdges or [pos2, pos1] == illegalEdges):
                continue

            # Only add to the open list if it's not expanded yet
            if not tuple(childPosition) in closedList:
            
                # copyAvailableItem               
                copy_available_item = curr_available.copy()

                # deduct from item list if it was required
                if itemRequired:
                    copy_available_item = deductItem(copy_available_item, itemRequired)

                childRaftSate = raftState
                
                # updating child raftstate based on where current child is
                # and the item required to get to the child.
                if itemRequired == 'r':
                    childRaftSate = 1
                
                elif childRaftSate == 1 and element != '~':
                    childRaftSate = 0
                
                # updating the stone coordinate that was used for child.
                # append to the parent ones.
                stoneCoord = []
                if itemRequired == 'o':
                    stoneCoord = [childPosition]
                    #print(stoneCoord)
                    copyStonePlaced += stoneCoord       
                
                # creating new child node and push to the openlist
                childNode = PathNode(tuple(childPosition), copy_available_item, cost + actionCost, curr_node, childRaftSate)
                childNode.addStonePlaced(copyStonePlaced)
                openList.push(childNode, childNode.cost + graph.getHCost(childPosition, goal))

    
    # intialize the returning variables
    path = []
    totalItemUsed = []
    totalNewItemCollected = []
    itemUsedState = False
    finalItemList = itemsAvailable
    finalRaftState = 1
    finalStonePlace = []

    # if we arrive goal, we are updating those variables.
    if position == goal_tuple:
        finalItemList = goalNode.getItemAvailable()    
        itemUsedState = confirmItemUsed(finalItemList, itemsAvailable)
        finalRaftState = goalNode.getRaftState()   
        finalStonePlace = goalNode.getStonePlaced()     

        # Ensure a path has been found
        position_list = list(position)
        
        path.insert(0, position_list)
        while position and position != start_tuple:
            position = closedList[position]
            position_list = list(position)
            path.insert(0, position_list)

    return [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace]

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# confirmItemUsed
# This function compares two item dictionaries and see whether they have the same counting or not
#---------------------------------------------------------------------------------------------------------------------------------------------------#

def confirmItemUsed(finalItems, itemsAvailable):
    itemsList = ['r','o', 'k', 'a']
    result = False
    for item in itemsList:
        if finalItems[item] != itemsAvailable[item]:
            result = True
            return result

    return result


#---------------------------------------------------------------------------------------------------------------------------------------------------#
# incrementDict
# increment dictionary expect the permenant item
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def incrementDict( user_dict, item):
    permenantItemList = {'a', 'k'}
    
    if item in user_dict and item not in permenantItemList:
        user_dict[item] += 1
    else:
        user_dict[item] = 1
    return user_dict

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# deductItem
# decrement dictionary expect the permenant item
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def deductItem( itemDict, item):
    
    permenantItemList = {'a', 'k'}
    if item and item not in permenantItemList:
        itemDict[item] -= 1
        
    return itemDict

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# astarItemsMultiPath
# astar items but returning the lists of PathNode itself.
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def astarItemsMultiPath(graph, start, goal, itemsAvailable, initialRaftState, illegalEdges):
    
    #itemsAvailable = intialItems.copy()
    #print("initial state") print(itemsAvailable)

    # Fringe. Nodes not visited yet
    openList = PriorityQueue()

    # Visited Nodes. Each one will store it's parent position
    closedList = {}
    nodeTable = {}


    # assign some start and goal points
    # and push start point as a node to openList.
    start_tuple = tuple(start)
    goal_tuple = tuple(goal)
    node = PathNode(start_tuple, itemsAvailable.copy())
    node.setRaftState(initialRaftState)
    openList.push(node)

    
    while openList:
        
        # if openList does not contain any node
        # we will break.     
        curr_node, _ = openList.pop()    
        if not curr_node:
            break
        
        position, cost = curr_node.position, curr_node.cost

        if position in closedList:
            # Oops. Already expanded.
            continue

        # Save the node in the closed list, and keep track of its parent
        if curr_node.parent != None:
            closedList[position] = curr_node.parent.position
        else:
            closedList[position] = curr_node.position

        #track of its items remainings
        nodeTable[position] = curr_node
        
        # arrived to goal so save it as goal node.
        if position == goal_tuple:
            goalNode = curr_node
            break
            
        # copy some parent properties
        curr_available = curr_node.getItemAvailable()
        raftState = curr_node.getRaftState()
        parentStonePlace = curr_node.getStonePlaced().copy()
        
        # for each legal child for current parent,
        for childPosition, actionCost, itemRequired, element in graph.getChildren(position, curr_available, 
                                                                                  raftState,parentStonePlace):
            copyStonePlaced = parentStonePlace.copy()

            # if illegal edges were given 
            # and current one is illegal, ignore current child.
            pos1 = list(position).copy()
            pos2 = childPosition
            if illegalEdges and ([pos1, pos2] in illegalEdges or [pos2, pos1] in illegalEdges):
                continue

            # Only add to the open list if it's not expanded yet
            if not tuple(childPosition) in closedList:
            
                # copyAvailableItem               
                copy_available_item = curr_available.copy()

                # deduct from item list if it was required
                if itemRequired:
                    copy_available_item = deductItem(copy_available_item, itemRequired)

                childRaftSate = raftState
                
                # updating child raftstate based on where current child is
                # and the item required to get to the child.
                if itemRequired == 'r':
                    childRaftSate = 1
                
                elif childRaftSate == 1 and element != '~':
                    childRaftSate = 0
                
                # updating the stone coordinate that was used for child.
                # append to the parent ones.
                stoneCoord = []
                if itemRequired == 'o':
                    stoneCoord = [childPosition]
                    #print(stoneCoord)
                    copyStonePlaced += stoneCoord       
                
                # creating new child node and push to the openlist
                childNode = PathNode(tuple(childPosition), copy_available_item, cost + actionCost, curr_node, childRaftSate)
                childNode.addStonePlaced(copyStonePlaced)
                openList.push(childNode, childNode.cost + graph.getHCost(childPosition, goal))

    
    # intialize the returning variables
    path = []
    totalItemUsed = []
    totalNewItemCollected = []
    itemUsedState = False
    finalItemList = itemsAvailable
    finalRaftState = 1
    finalStonePlace = []

    # if we arrive goal, we are updating those variables.
    if position == goal_tuple:
        finalItemList = goalNode.getItemAvailable()    
        itemUsedState = confirmItemUsed(finalItemList, itemsAvailable)
        finalRaftState = goalNode.getRaftState()   
        finalStonePlace = goalNode.getStonePlaced()     

        # Ensure a path has been found
        position_list = list(position)
        
        path.insert(0, position_list)
        while position and position != start_tuple:
            position = closedList[position]
            position_list = list(position)
            path.insert(0, position_list)

    return [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable] #finalItemList, ]
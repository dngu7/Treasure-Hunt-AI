from pqueue import PriorityQueue


############### Acknowledgement ###############
# Resource: https://raw.githubusercontent.com/ichinaski/astar/master/astar.py
# - resource used are: graph, astar and node class



############### Garph Implementation ###############
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

def manhattan(start, goal):
    
    
    x1,y1 = start
    x2,y2 = goal
    
    return abs(x1 - x2) + abs(y1 - y2)


# inherit graph class to suit our global agent map.        
class AstarMap(Graph):
    
    
    requiredItems = {'-' : 'k', 'T' : 'a'}
    
    def __init__(self, grid, agentState = 0):
        self.grid = grid
        if len(grid) >= len(grid[0]):
            self.size = len(grid)
        else:
            self.size = len(grid[0])
        self.agentState = agentState
        
    # create nodes connections.
    def updateGrid(self, newGrid, agentState = []):
        self.grid = newGrid
        self.agentState = agentState
        
        
    # updating states such as on raft state
    def updateState(self, newState):
        self.agentState = newState 
        
    # get raft state
    def getRaftState(self):
        return self.agentState
        
    # calculate manhattan and return
    def getHCost(self, start, goal):
        hcost = manhattan(start,goal)
        return hcost
    
    # get all legal children at current point
    # get children will return
    # the lists contatining
    # [d, cost, item]
    # where 
    # d - the position index in grid
    #   - d[0] represents row while d[1] represents column
    # cost - the cost to get on to the current position to the neighbour one
    #      - will be always 1.
    # item - gives what sort of items it needs in order to get to the neighbour one
    def getChildren(self, point, itemAvailable, currRaftState):
        y,x = point
    
        # find all indices that is neibour to current point
        neighbours = []
        for i,j in [ [-1, 0], [1, 0], [0, -1], [0, 1] ]:
            
            currI = y + i
            currJ = x + j
            if currI >= 0 and currI < self.size  and currJ >= 0 and  currJ < self.size:
                neighbours.append( [currI, currJ] )

        #print("all neighbours")
        #print(indexList)

        legalNeighbours = []
        # find all legal neighbours
        for direction in neighbours:
            
            # if crossing to one of neibbour is legal,
            # add on to the legalNeighbours lists
            if self.checkLegalState(direction, itemAvailable, currRaftState ):
                element = self.grid[direction[0]][direction[1]]
                itemRequired = self.getItemRequired(direction, itemAvailable, currRaftState)
                cost2Cross = 1 # assuming cost to go to next index is always one.
                legalNeighbours.append( [direction, cost2Cross, itemRequired, element] )
                  
        return legalNeighbours


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
        
            #print("current itemAvailable seeing")
            #print(itemAvailable)    
            
            if raftState:
                #print("on the raft")
                return {}
            elif 'o' in itemAvailable and itemAvailable['o'] >= 1:
                return 'o'
            elif 'r' in itemAvailable and itemAvailable['r'] >= 1:
                return 'r'
        else:
            return []
     
    # return the item when it needs to collect
    # by consequence of getting there
    def getItemCollected(self, d):
        
        element = self.grid[d[0]][d[1]]
        itemlists = {'k', 'o', 'a','$'}
        if element in itemlists:
            return element
            
        elif element == 'T':
            return 'r'
        return {}

    # get raft state
    def getRaftState(self):
        return self.agentState

    # this function will return true or false
    # for the check whether it has legal path 
    # for the a_star algorithm
    def checkLegalState(self, d,items, currRaftState):

        raftState = currRaftState
        element = self.grid[d[0]][d[1]]
        
        obstacles = ['~', 'T', '-', '*', '?','.']


        # if we are already on the raft or 
        # have items to cross water
        if (element  == '~' and (raftState == 1 or ('r' in items and items['r'] > 0) 
                                    or ('o' in items and items['o'] > 0 ) ) ):
            #if raftState == 1:
            #    print("raft found")
            return 1
            
        # if we have key and door is the neighbour
        elif (element == '-' and 'k' in items and items['k'] > 0 ):
            return 1
        # if we have axe to cut down the tree
        elif (element == 'T' and 'a' in items and items['a'] > 0 ):
            return 1

        # if the neighbour is not obstacles
        elif (element not in obstacles ):
            return 1
        
        # Otherwise illegal
        else:
          return 0


############### Astar Implementations ###############


class Node:
    def __init__(self, position, cost=0, parent=None):
        # State representation. It can be a tuple, an integer, 
        # or any data structure that holds your current state for this node
        self.position = position
        self.cost = cost
        self.parent = parent
        
# this class will implement node class but specific to our problem.
class PathNode(Node):
    def __init__(self, position, itemAvailable = {}, cost = 0, parent=None, raftState = 0):
    
        Node.__init__(self, position, cost, parent)
        self.raftState = raftState
        self.itemAvailable = itemAvailable
        self.newItemsCollected = {}
        #self.element = element
        
    def getItemsCollectedSofar(self):
        return self.newItemsCollected
        
    def setItemCollected(self, itemCollectedList):
        self.newItemsCollected = itemCollectedList
        
    def addNewItems2Collected(self, newItem):
        if newItem in self.newItemsCollected:
            self.newItemsCollected[newItem] += 1
        else:
            self.newItemsCollected[newItem] = 1
        
    def getItemAvailable(self):
        return self.itemAvailable

    # get raft state
    def getRaftState(self):
        return self.raftState

    def setRaftState(self, raftState):
        self.raftState = raftState


        
 

def astarItems(graph, start, goal, itemsAvailable, initialRaftState):
    
    #itemsAvailable = intialItems.copy()

    #print("initial state")
    #print(initialRaftState)
    # Fringe. Nodes not visited yet
    openList = PriorityQueue()

    # Visited Nodes. Each one will store it's parent position
    closedList = {}

    start_tuple = tuple(start)
    goal_tuple = tuple(goal)
    
    node = PathNode(start_tuple, itemsAvailable.copy())
    node.setRaftState(initialRaftState)
    openList.push(node)

    
    while openList:
        
        #print("entered in open list loop")        
        curr_node, _ = openList.pop()
        
        if not curr_node:
            break
        
        #print("poped openlist") 
        position, cost = curr_node.position, curr_node.cost

        if position in closedList:
            # Oops. Already expanded.
            continue

        # Save the node in the closed list, and keep track of its parent
        if curr_node.parent != None:
            closedList[position] = curr_node.parent.position
        else:   
            closedList[position] = curr_node.position
            
        if position == goal_tuple:
            goalNode = curr_node
            break
            
        #print("curr position")
        #print(position)
            
        curr_available = curr_node.getItemAvailable()
        itemCollectedList = curr_node.getItemsCollectedSofar()
        raftState = curr_node.getRaftState()
        #print("currently available item origin:")
        #print(curr_available) 
        
        for childPosition, actionCost, itemRequired, element in graph.getChildren(position, curr_available, raftState):
        
            #print("neibour position:", childPosition)
        
            # Only add to the open list if it's not expanded yet
            if not tuple(childPosition) in closedList:
            
                # copyAvailableItem               
                copy_available_item = curr_available.copy()

                if itemRequired:
                    copy_available_item = deductItem(copy_available_item, itemRequired)

                childRaftSate = raftState
                
                if itemRequired == 'r':
                    
                    #print('raft set at')
                    #print(childPosition)
                    
                    childRaftSate = 1
                
                elif childRaftSate == 1 and element != '~':
                    #print("item remaining")
                    #print(copy_available_item)
                    #print('raft reset at')
                    #print(childPosition)
                    childRaftSate = 0
                
                    
                
                # creating new child node and push to the openlist
                childNode = PathNode(tuple(childPosition), copy_available_item, cost + actionCost, curr_node, childRaftSate)
                openList.push(childNode, childNode.cost + graph.getHCost(childPosition, goal))

    path = []
    totalItemUsed = []
    totalNewItemCollected = []
    itemUsedState = False
    finalItemList = []
    finalRaftState = []
    if position == goal_tuple:
        finalItemList = goalNode.getItemAvailable()    
        itemUsedState = confirmItemUsed(finalItemList, itemsAvailable)
        finalRaftState = goalNode.getRaftState()
        #print("final Item available:")
        #print(goalNode.getItemAvailable())
        

        # Ensure a path has been found
        position_list = list(position)
        
        path.insert(0, position_list)
        while position and position != start_tuple:
            position = closedList[position]
            position_list = list(position)
            path.insert(0, position_list)

    return [path, itemUsedState, finalItemList] #finalItemList, raftState]
    
def confirmItemUsed(finalItems, itemsAvailable):
    itemsList = ['r','o', 'k', 'a']
    '''
    
    print("initial Item available:")
    print(itemsAvailable)

    print("final Item available:")
    print(finalItems)
    '''

    result = False
    for item in itemsList:
        if finalItems[item] != itemsAvailable[item]:
            result = True
            return result

    return result
    
def incrementDict( user_dict, item):
    permenantItemList = {'a', 'k'}
    
    if item in user_dict and item not in permenantItemList:
        user_dict[item] += 1
    else:
        user_dict[item] = 1
    return user_dict
    
def deductItem( itemDict, item):
    
    permenantItemList = {'a', 'k'}
    #print("items")
    #print(item)
    if item and item not in permenantItemList:
        itemDict[item] -= 1
        
    return itemDict
    
    
    


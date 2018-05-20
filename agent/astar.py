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
    
    def __init__(self, grid, agentState = [0]):
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
        return self.agentState[0]
        
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
    def getChildren(self, point, itemAvailable):
        y,x = point
    
        # find all indices that is neibour to current point
        indexList = []
        for i,j in [ [-1, 0], [1, 0], [0, -1], [0, 1] ]:
            
            currI = y + i
            currJ = x + j
            if currI >= 0 and currI < self.size  and currJ >= 0 and  currJ < self.size:
                indexList.append( [currI, currJ] )

        #print("all neighbours")
        #print(indexList)

        legalNeighbours = []
        # find all legal neighbours
        for d in indexList:
            
            # if crossing to one of neibbour is legal,
            # add on to the legalNeighbours lists
            if self.checkLegalState(d, itemAvailable ):
                
                itemUsed = self.getItemRequired(d, itemAvailable)
                itemCollected = self.getItemCollected(d)
                legalNeighbours.append( [d, 1, itemUsed, itemCollected] )
                  
        return legalNeighbours


    def getItemRequired(self, d, itemAvailable):
    
        element = self.grid[d[0]][d[1]]
        itemlists = {'k', 'o', 'a', 'r', '$'}
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
        elif element == '~' and not isempty(itemAvailable):
            if raftState:
                return []
            elif 'o' in itemAvailable:
                return 'o'
            elif 'r' in itemAvailable:
                return 'r'
        else:
            return []
     
    # return the item when it needs collect
    # by consequence of getting there
    def getItemCollected(self, d):
        
        element = self.grid[d[0]][d[1]]
        itemlists = {'k', 'o', 'a', 'r', '$'}

        if element in itemlists:
            return element

        return []

    # this function will return true or false
    # for the check whether it has legal path 
    # for the a_star algorithm
    def checkLegalState(self, d,items):

        raftState = self.getRaftState()
        element = self.grid[d[0]][d[1]]
        
        obstacles = ['~', 'T', '-', '*']


        # if we are already on the raft or 
        # have items to cross water
        if (element  == '~' and (raftState == 1 or ('r' in items and items['r'] > 0) 
                                    or ('o' in items and items['o'] > 0 ) ) ):
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
    def __init__(self, position, itemAvailable = {}, cost = 0, parent=None, raftState = 0, itemsUsed = {}):
    
        Node.__init__(self, position, cost, parent)
        self.raftState = raftState
        self.itemsUsed = itemsUsed
        self.itemAvailable = itemAvailable
        self.newItemsCollected = {}
        #self.element = element
        
    def getItemsUsedSofar(self):
        return self.itemsUsed
        
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
        
 

def astarItems(graph, start, goal, itemsAvailable):
    # Fringe. Nodes not visited yet
    openList = PriorityQueue()

    # Visited Nodes. Each one will store it's parent position
    closedList = {}

    start_tuple = tuple(start)
    goal_tuple = tuple(goal)

    node = PathNode(start_tuple, itemsAvailable)
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
        
        #print("currently available item origin:")
        #print(curr_available) 
        
        for childPosition, actionCost, itemRequired, itemCollected in graph.getChildren(position, curr_available):
        
            #print("neibour position:", childPosition)
        
            # Only add to the open list if it's not expanded yet
            if not tuple(childPosition) in closedList:
            
                # updating the items used to get to the child position
                itemUsedList = curr_node.getItemsUsedSofar()
                itemCollectedList = curr_node.getItemsCollectedSofar()
                
                copy_available_item = curr_available
                if itemRequired:
                                            
                    itemUsedList = incrementDict(itemUsedList, itemRequired)
                    copy_available_item = curr_available
                    copy_available_item[itemRequired] -= 1
                    
                if itemCollected:
                    #print("currently available item")
                    #print(copy_available_item)
                    itemCollectedList = incrementDict(itemCollectedList, itemCollected)
                    #print("Item collected:")
                    #print(itemCollectedList)
                    copy_available_item = incrementDict(copy_available_item, itemCollected)
                
                raftState = 0
                if itemUsedList and 'r' in itemUsedList and itemUsedList['r'] > 0:
                    raftState = 1
                
                
                # creating new child node and push to the openlist
                childNode = PathNode(tuple(childPosition), copy_available_item, cost + actionCost, curr_node, raftState, itemUsedList)
                childNode.setItemCollected(itemCollectedList)
                openList.push(childNode, childNode.cost + graph.getHCost(childPosition, goal))

    path = []
    totalItemUsed = []
    totalNewItemCollected = []
    
    if position == goal_tuple:
        totalItemUsed = goalNode.getItemsUsedSofar()
        totalNewItemCollected = goalNode.getItemsCollectedSofar()
        print("totalItemUsed:")
        print(totalItemUsed)
        
        print("totalNewItemCollected:")
        print(totalNewItemCollected)
        
        # Ensure a path has been found
        position_list = list(position)
        
        path.insert(0, position_list)
        while position and position != start_tuple:
            position = closedList[position]
            position_list = list(position)
            path.insert(0, position_list)

    return [path,  totalItemUsed, totalNewItemCollected]
    
    
    
def incrementDict( user_dict, item):

    
    if item in user_dict:
        user_dict[item] += 1
    else:
        user_dict[item] = 1
    return user_dict
    
    
    
    
    

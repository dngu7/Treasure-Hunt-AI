#!/usr/bin/python


# Resource: https://gist.githubusercontent.com/jamiees2/5531924/raw/0e874f39d43246e3a10c38cb2e9c0457c791cacb/astar.py

       
def children(point,grid, raftState):
    y,x = point
    
    # find all indices that is neibour to current point
    indexList = []
    for i in [-1, 1]
        for j in [-1,1]        
            currI = y + i
            currJ = x + j
            if currI >= 0 and currI < 160  and currJ >= 0 and  currJ < 160
                indexList.append( [currI, currJ] )

    # find all legal neighbours
    legalNeighbours = [d for d in indexList if checkLegalState(grid, d, raftState)]


    return legalNeighbours
    
# this function will return true or false
# for the check whether it has legal path 
# for the a_star algorithm
def checkLegalState(grid, d, raftState):

    element = grid[d[0]][d[1]]

    # if we are already on the raft and 
    # the neibour element is water, 
    # we include in the final lists.
    if (element  == '~' and raftState = 1)
        return 1
        
    # if the neighbour is not water or wall
    elif (element  != '~' and element != '*') 
        return 1
    
    # Otherwise illegal
    else
      return 0

# manhattan heuristics
def manhattan(point,point2):
    
    x1,y1 = point
    x2,y2 = point2
    
    return abs(x1 - x2) + abs(y1 - y2)
    
    
def aStar(start, goal, grid):


    G = [] 
    H = []
    
    
    #The open and closed sets
    openset = set()
    closedset = set()
    #Current point is the starting point
    current = start
    #Add the starting point to the open set
    openset.add(current)
    #While the open set is not empty
    while openset:
        #Find the item in the open set with the lowest G + H score
        current = min(openset, key=lambda idx : G[idx[0]][idx[1]] + H[idx[0]][idx[1]])
        #If it is the item we want, retrace the path and return it
        if current == goal:
            path = []
            while current.parent:
                path.append(current)
                current = current.parent
            path.append(current)
            return path[::-1]
            
        #Remove the item from the open set
        openset.remove(current)
        #Add it to the closed set
        closedset.add(current)
        #Loop through the node's children/siblings
        for node in children(current,grid):
            #If it is already in the closed set, skip it
            if node in closedset:
                continue
            #Otherwise if it is already in the open set
            if node in openset:
                #Check if we beat the G score 
                new_g = current.G + current.move_cost(node)
                if node.G > new_g:
                    #If so, update the node to have a new parent
                    node.G = new_g
                    node.parent = current
            else:
                #If it isn't in the open set, calculate the G and H score for the node
                node.G = current.G + current.move_cost(node)
                node.H = manhattan(node, goal)
                #Set the parent to our current item
                node.parent = current
                #Add it to the set
                openset.add(node)
    #Throw an exception if there is no path
    raise ValueError('No Path Found')
    

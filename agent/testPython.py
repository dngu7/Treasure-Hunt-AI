#!/usr/bin/python

from pprint import pprint



# Arguments:
# note: all map should be in character type array.
# 1) viewmap - it is assumed to be always 5 by 5.
# 2) GlobalMap - it is assumed to be 160 by 160
# 3) CurrPos - current index of agent position
# Returns:
# 1) CurrAgentDir - indicating the directions of Agent.
def updateGlobalMap(viewmap, CurrPos ):
    global agentMap
    
    N = 5
    M = 160
    
    # current position of a agent in the 
    # global map.
    curr_i = CurrPos[0] 
    curr_j = CurrPos[1]
    
    
    # looping around the view map to copy into
    # GlobalMap
    for i in range(N):
        for j in range(N):
            element = viewmap[i][j]
            
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
                
                agentMap[Iidx][Jidx] = element
            
           # else if the current viewmap reading is at the centre,
           # that is stored as agent directions.  

                
    
                
# Reference: https://artemrudenko.wordpress.com/2014/08/28/python-rotate-2d-arraymatrix-90-degrees-one-liner/
def rotate(matrix, degree):
    if abs(degree) not in [0, 90, 180, 270, 360]:
        # raise error or just return nothing or original
    if degree == 0:
        z = matrix
    elif degree > 0:
        z = rotate(zip(*matrix[::-1]), degree-90)
    else:
        z = rotate(zip(*matrix)[::-1], degree+90)
        
    matrix = [list(a) for a in z]
    
    return matrix

def printGlobal():
    for i in range(160):
            print("line %3d" %(i), end="" )
            for j in range(100):
                if i == currAgentPos[0] and j == currAgentPos[1]:
                    print('^', end = "")
                else:
                    print(agentMap[i][j], end='')
            print('')
            

def updateViewMap(viewmap, wholeMap, currPos)

    startI = currPos[0]-2
    startJ = currPos[1]-2
    
    i = 0
    j = 0
    for I in range(startI, startI+5):
        for J in range(startJ, startJ + 5):
            viewmap[i][j] =  wholeMap[I][J]
            j = j+1    
        
        j = 0        
        i = i +1

    return viewmap


def main():

    file = open("map_example.txt", "r");
 
    str =  file.read() 

    #viewmap = []
    
    w, h = 80, 80;
    wholeMap = [[' ' for x in range(w)] for y in range(h)]
    
    w, h = 160, 160;
    global agentMap
    agentMap = [[' ' for x in range(w)] for y in range(h)]

    w, h = 5, 5;
    viewmap = [[' ' for x in range(w)] for y in range(h)]

    currPos = [0, 0]

    i = 0
    j = 0
    
    for letter in str:
        
        
        if letter != '\n':
        
            if (letter == '^' or letter == '<'
                or letter == '>' or letter == 'v'):
                currPos[0] = i
                currPos[1] = j
                 
        
            wholeMap[i][j] = letter
            j = j +1
        else:
            i = i +1
            j  = 0
           
    
    currAgentPos = [80,80]
    viewmap = updateViewMap(viewmap, wholeMap, currPos)
    pprint( viewmap)    
    updateGlobalMap(viewmap, currAgentPos )
    
    
    currAgentPos = [80,81]
    viewmap = updateViewMap(viewmap, wholeMap, currPos)
    pprint( viewmap)    
    updateGlobalMap(viewmap, currAgentPos )
    
    
    #pprint( agentMap)
    
    #for i in range(0,159):
     #   print( agentMap[i])
     
    
        
        
            


if __name__ == "__main__":
    main()
  
                

    
    
    

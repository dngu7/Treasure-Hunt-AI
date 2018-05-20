
from astar import AstarMap, astarItems


def main():

    file = open("allmap.txt", "r");
 
    str =  file.read() 
    
    w, h = 24, 10;
    wholeMap = [[' ' for x in range(w)] for y in range(h)]
    
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
            
    
    globalMap = AstarMap(wholeMap)
    
    print(currPos)
    
    goal = [6, 16]
    
    itemsAvailable = {}
    
    [path, itemsUsed, itemCollected] =  astarItems(globalMap, currPos, goal, itemsAvailable)
    
    print(path)
    print(itemCollected)
    
    print(wholeMap[5][11])
    
if __name__ == "__main__":
    main()

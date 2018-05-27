from astar import astarItems, AstarMap, astarItemsMultiPath
from operator import itemgetter

def globalmap_edges(self, globalmap):
    edges = []
    size = 160

    blocks = ['T','*','-','.']
    moves = [(0,1), (1,0),(0,-1),(-1,0)]

    for i in size:
        for y in size:
            if globalmap[i][y] in blocks:
                continue
            for move in moves:
                move_x = move[0] + i
                move_y = move[1] + y
                newedge = [[i,y], [move_x,move_y]]
                reverseedge = [[move_x,move_y], [i,y]]

                if move_x in range(0,size) and move_y in range(0,size)
                    and globalmap[move_x][move_y] not in blocks and reverseedge not in edges:
                    edges.append(newedge)
    
    return edges
                    
def converttoedges(path):
    length = len(path)
    edges = []
    for i in range(length-1):
        edge = [path[i],path[i+1]]
        revedge = [path[i+1],path[i]]
        edges.append(edge)
        edges.app[end(revedge)]

    return edges



def YenKSP(globalmap, source, destination, itemlist, onRaft):
    # Storage
    solspace = []
    Bspace = []
    illegaledges = []
    K = 10
    #Find the shortest path using astar
    # return [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable]

    solspace[0] = astarItemsMultiPath(globalmap, source, destination, itemlist, onRaft, illegaledges)

    for k in range(1,K):
        for i in range(len(A[k - 1]) - 2):
            spurNode = solspace[k-1][0][i]
            rootPath = solspace[k-1][0][0:i+1]
            spurTuple = tuple(spurNode])
            spurItemList = solspace[k-1][5][spurTuple].getItemAvailable()
            spurRaft = solspace[k-1][5][spurTuple].getRaftState()

            for shortPath in solspace:
                if rootPath == shortPath[0:i+1]:
                    illegaledges.append([i+1,i+2])   

            rootedges = converttoedges([rootPath[:-1]])
            for edge in rootedges:
                illegaledges.append(edge)


            astar_result = astarItemsMultiPath(globalmap, spurNode, destination, spurItemList, spurRaft, illegaledges)

            if len(astar_result[0]) == 0:
                illegaledges = []
                continue

            totalPath = rootPath + astar_result[0]
            astar_result[0] = totalPath
            Bspace.append(astar_result)
            illegaledges = []
        if len(Bspace) == 0:
            break

        Bspace.sort() #sort by number of stones used and length of path
        sorted(Bspace, key=itemgetter(4,0))
        solspace[k] = B[0]
        
        Bspace.pop()
    #print(solspace)
    return solspace





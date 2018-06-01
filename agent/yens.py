# Hybrid implementation of Yens-Astar adapted for this game. 

from astar import astarItems, AstarMap, astarItemsMultiPath
from operator import itemgetter
import heapq

                   
def converttoedges(path):
    length = len(path)
    edges = []
    for i in range(length-1):
        edge = [path[i],path[i+1]]
        revedge = [path[i+1],path[i]]
        edges.append(edge)
        edges.append(revedge)

    return edges

def YenAstarMultiPath(globalmap, source, destination, itemlist, onRaft):
    # return [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable]

    Astar_Map = AstarMap(globalmap)
    #Find the shortest path using astar
    testPaths = []
    illegaledges = []
    visitededges = {}
    exploredPaths = {}
    pathSpace = []
    astarpath = astarItemsMultiPath(Astar_Map, source, destination, itemlist, onRaft, illegaledges)
    heapq.heappush(testPaths,(1,astarpath))
    exploredPaths[str(astarpath[4])] = astarpath
    obstacle = globalmap[destination[0]][destination[1]]


    while testPaths:
        cost, current_path = heapq.heappop(testPaths)
        stoneCombination = current_path[4]

        for i in range(len(current_path[0])-1):
            rootPath = current_path[0][0:i+1]
            spurNode = current_path[0][i]
            spurTuple = tuple(spurNode)
            spurNodes = current_path[5]
            spurItemList = current_path[5][spurTuple].getItemAvailable()
            spurRaft = current_path[5][spurTuple].getRaftState()
            spurStoneCombo = current_path[5][spurTuple].getStonePlaced()
            fwdPath = current_path[0][i+1:]
            illegaledges = []

            visitededges.setdefault(str(spurNode),[]).append(current_path[0][i+1])
            visitededges.setdefault(str(current_path[0][i+1]),[]).append(spurNode)

            #limits number of branches to 3 best paths from spurnode
            if len(visitededges[str(spurNode)]) > 3:
                continue

            rootedges = converttoedges(rootPath)
            for edge in rootedges:
                illegaledges.append(edge)

            for edge in visitededges[str(spurNode)]:
                illegaledges.append([spurNode, edge])
            
            astar_result = astarItemsMultiPath(Astar_Map, spurNode, destination, spurItemList, spurRaft, illegaledges)

            newfwdpath = astar_result[0][1:]
            totalPath = rootPath + newfwdpath
            newStoneCombo = astar_result[4]
            totalStoneCombo = spurStoneCombo + newStoneCombo

            if len(astar_result[0]) == 0:
                continue
            else:
                #print("\n---\nCurrPath derived: {}".format(current_path[0]))
                astar_result[0] = totalPath
                astar_result[5] = {**spurNodes, **astar_result[5]}
                #print("stonecombo: {}".format(totalStoneCombo))
                #print("rootPath {}  \nspurNode {}  \nitems at spurnode {}\nnewforwardPath {}".format(rootPath, spurNode, spurItemList, newfwdpath))
                #print("Current SpurNode Expansions: {}".format(visitededges[str(spurNode)]))
                #print("illegaledges: {}".format(illegaledges))
                if totalPath not in pathSpace:
                    pathSpace.append(totalPath)
                    if (str(totalStoneCombo) not in exploredPaths) or (str(totalStoneCombo) in exploredPaths) and (len(exploredPaths[str(totalStoneCombo)][0]) > len(totalPath)):
                        #print("** Path added to exploredpath: \n{}\n----".format(totalPath))
                        exploredPaths[str(totalStoneCombo)] = astar_result
                        heapq.heappush(testPaths, (len(totalPath) * 0.1 + len(astar_result[4]) * 10, astar_result))
                    else:
                        heapq.heappush(testPaths, (len(totalPath) * 0.1 + len(astar_result[4]) * 10, astar_result))
                    
                            

    print("\n\nEXPLORED PATHS SENT")
    finalpathlist = []
    leaststonesused = min(len(i) for i in exploredPaths)

    for stonecombo in exploredPaths:
        if len(stonecombo) == leaststonesused:
            if obstacle == 'o':
                exploredPaths[stonecombo][2]['o'] += 1
            finalpathlist.append(exploredPaths[stonecombo])
            print("Stone Used {} finalItems {} | Path {}".format(stonecombo, exploredPaths[stonecombo][2], exploredPaths[stonecombo][0]))
        

    return finalpathlist





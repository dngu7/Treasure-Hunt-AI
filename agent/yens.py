#!/usr/bin/python3.6
#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Yens.py
# Hybrid Implementation of Yens's Algorithm and Astar Search adapted for this game
# This adaption is a modification from the pseudocode found from the wikipedia page below (which uses Djistra's intead)
# Source: https://en.wikipedia.org/wiki/Yen%27s_algorithm
#---------------------------------------------------------------------------------------------------------------------------------------------------#


from astar import astarItems, AstarMap, astarItemsMultiPath
from operator import itemgetter
import heapq

# Converts a path into a list of edges                   
def converttoedges(path):
    length = len(path)
    edges = []
    for i in range(length-1):
        edge = [path[i],path[i+1]]
        revedge = [path[i+1],path[i]]
        edges.append(edge)
        edges.append(revedge)

    return edges

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# YenAstarMultiPath
# Takes a start and destination coordinate and returns a list of all possible stone placement combinations and their respective shortest 
# path from source to destination (which use those stone placements)
#---------------------------------------------------------------------------------------------------------------------------------------------------#

def YenAstarMultiPath(globalmap, source, destination, itemlist, onRaft):

    Astar_Map = AstarMap(globalmap)
    testPaths = []
    illegaledges = []
    visitededges = {}
    exploredPaths = {}
    pathSpace = []

    #Generate an intial astar path to build off. 
    astarpath = astarItemsMultiPath(Astar_Map, source, destination, itemlist, onRaft, illegaledges)
    heapq.heappush(testPaths,(1,astarpath))

    #Store the intial paths in a hashtable using stone placements as a key
    exploredPaths[str(astarpath[4])] = astarpath
    obstacle = globalmap[destination[0]][destination[1]]


    while testPaths:
        cost, current_path = heapq.heappop(testPaths)
        stoneCombination = current_path[4]

        #Generate spur nodes which range from the first node to the next to last node in the popped path
        for i in range(len(current_path[0])-1):
            #rootPath are the nodes from first node to the spurnode
            rootPath = current_path[0][0:i+1]
            #SpurNode generated from path
            spurNode = current_path[0][i]
            spurTuple = tuple(spurNode)


            #Nodes from astar can be unpacked to find the items, raft state and stone combinations at various points in the path
            #These are used to generate future paths starting from the spur node. 
            spurNodes = current_path[5]
            spurItemList = current_path[5][spurTuple].getItemAvailable()
            spurRaft = current_path[5][spurTuple].getRaftState()
            spurStoneCombo = current_path[5][spurTuple].getStonePlaced()
            illegaledges = []

            #Builds a hashtable containing all visited edges between nodes using the current path and spur path
            visitededges.setdefault(str(spurNode),[]).append(current_path[0][i+1])
            visitededges.setdefault(str(current_path[0][i+1]),[]).append(spurNode)

            #limits number of branches to 3 best paths from spurnode
            if len(visitededges[str(spurNode)]) > 4:
                continue

            #Add rootpath to illegal edges in avoid looping
            rootedges = converttoedges(rootPath)
            for edge in rootedges:
                illegaledges.append(edge)

            #Add popped path's spurnode extention to illegal edges in avoid duplicate
            for edge in visitededges[str(spurNode)]:
                illegaledges.append([spurNode, edge])
            
            #Generate new path which prevents illegal edges from being generated 
            astar_result = astarItemsMultiPath(Astar_Map, spurNode, destination, spurItemList, spurRaft, illegaledges)

            newfwdpath = astar_result[0][1:]
            totalPath = rootPath + newfwdpath
            newStoneCombo = astar_result[4]
            totalStoneCombo = spurStoneCombo + newStoneCombo

            if len(astar_result[0]) == 0:
                continue
            else:
                astar_result[0] = totalPath
                #Combine node information across all paths
                astar_result[5] = {**spurNodes, **astar_result[5]}

                if totalPath not in pathSpace:
                    pathSpace.append(totalPath)
                    #Store only the shortest paths for unique stone placement combinations. Push all pathhs onto the Priority queue based on path length and stone count
                    if (str(totalStoneCombo) not in exploredPaths) or (str(totalStoneCombo) in exploredPaths) and (len(exploredPaths[str(totalStoneCombo)][0]) > len(totalPath)):
                        exploredPaths[str(totalStoneCombo)] = astar_result
                        heapq.heappush(testPaths, (len(totalPath) * 0.1 + len(astar_result[4]) * 10, astar_result))
                    else:
                        heapq.heappush(testPaths, (len(totalPath) * 0.1 + len(astar_result[4]) * 10, astar_result))
                    
    finalpathlist = []
    leaststonesused = min(len(i) for i in exploredPaths)
    #Return a list of shortest pathhs for each stone combination. Only the combinations with the least stones are returned. 
    for stonecombo in exploredPaths:
        if len(stonecombo) == leaststonesused:
            if obstacle == 'o':
                exploredPaths[stonecombo][2]['o'] += 1
            finalpathlist.append(exploredPaths[stonecombo])

    return finalpathlist





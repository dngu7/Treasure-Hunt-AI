from astar import astarItems, AstarMap, astarItemsMultiPath
from operator import itemgetter

                   
def converttoedges(path):
    length = len(path)
    edges = []
    for i in range(length-1):
        edge = [path[i],path[i+1]]
        revedge = [path[i+1],path[i]]
        edges.append(edge)
        edges.append(revedge)

    return edges



def YenMultiPath(globalmap, source, destination, itemlist, onRaft):
    # Storage
    
    Bspace = []
    illegaledges = []
    K = 10
    solspace = []
    Astar_Map = AstarMap(globalmap)
    #Find the shortest path using astar
    # return [path, itemUsedState, finalItemList, finalRaftState, finalStonePlace, nodeTable]

    solspace.append(astarItemsMultiPath(Astar_Map, source, destination, itemlist, onRaft, illegaledges))

    for k in range(1,K):
        
        for i in reversed(range(len(solspace[-1][0])-1)):
            
            


            rootPath = solspace[-1][0][0:i+1]
            
            spurNode = solspace[-1][0][i]
            spurTuple = tuple(spurNode)
            spurNodes = solspace[-1][5]
            spurItemList = solspace[-1][5][spurTuple].getItemAvailable()
            spurRaft = solspace[-1][5][spurTuple].getRaftState()

            fwdPath = solspace[-1][0][i+1:]
            
            illegaledges.append([spurNode,solspace[-1][0][i+1]])  

            #print("before spurnodes: {}".format(spurNodes))
            #print("spurNode {} fwdPath: {}".format(spurNode, fwdPath))
            #for i in fwdPath:
                #fwdTuple = tuple(i)
                #spurNodes.pop(fwdTuple,0)

            #print("after spurnodes: {}".format(spurNodes))

            rootedges = converttoedges(rootPath)
            for edge in rootedges:
                illegaledges.append(edge)
            

            astar_result = astarItemsMultiPath(Astar_Map, spurNode, destination, spurItemList, spurRaft, illegaledges)
            
            
            #print("illegaledges: {}\n".format(illegaledges))
            if len(astar_result[0]) == 0:
                illegaledges = []
                continue
            
            if len(astar_result[0]) > 0:
                newfwdpath = astar_result[0][1:]
                totalPath = rootPath + newfwdpath
                astar_result[0] = totalPath
                astar_result[5] = {**spurNodes, **astar_result[5]}
                
                if astar_result not in Bspace:
                    print("\n\n--- SolspaceCount {}, k: {} | i: {} ".format(len(solspace), k, i))
                    print("Solspace used: {}".format(solspace[-1]))
                    print("items at spurnode: {}".format(spurItemList))
                    print("rootPath {}  \nspurNode {}  \nforwardPath {}".format(rootPath, spurNode, newfwdpath))
                    print("Final path appended to Bspace: \n{}\n----".format(astar_result[0]))
                    Bspace.append(astar_result)

            illegaledges = []
        
        if len(Bspace) == 0:
            break

        #Bspace.sort() #sort by number of stones used and length of path
        sorted(Bspace, key=itemgetter(4,0))
        #print("")
        #for i in Bspace:
        #    print("{}".format(i))
        #print("")
        if Bspace[0] not in solspace:
            print("Bspace[0] appended to solspace: {}".format(Bspace[0]))
            solspace.append(Bspace[0])
        
        Bspace.pop()
    print("source: {} destination: {} \nFinal Solspace: {}\n".format(source, destination, solspace))
    return solspace





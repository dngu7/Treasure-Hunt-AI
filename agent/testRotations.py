#!/usr/bin/python

from pprint import pprint

def rotate(matrix, degree):
    if abs(degree) not in [0, 90, 180, 270, 360]:
        # raise error or just return nothing or original
        print(degree)
        return matrix
    if degree == 0:
        z = matrix
    elif degree > 0:
        z = zip(*matrix[::-1])
        matrix = [list(a) for a in z]
        matrix = rotate(matrix, degree-90)
    else:
        z = zip(*matrix)[::-1]
        matrix = [list(a) for a in z]
        matrix = rotate(matrix, degree+90)
        
    #matrix = [list(a) for a in z]
    
    return matrix
    
# https://stackoverflow.com/questions/8372399/zip-with-list-output-instead-of-tuple
    
def printMatrix(matrix):
    for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                print(matrix[i][j], end="")
            print('')
    
matrix = [[1,2,3], [4,5,6], [7,8,9]]


printMatrix( rotate(matrix, 270))

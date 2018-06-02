#!/usr/bin/python3.6

# Rotation function rotates a given matrix based in the degree provided
# In the agent, it is used to rotate the provided matrix from the game and convert it to 0 degrees (upward). 


from pprint import pprint

def rotate(matrix, degree):
    if abs(degree) not in [0, 90, 180, 270, 360]:
        # raise error or just return nothing or original
        #print(degree)
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
    return matrix
    

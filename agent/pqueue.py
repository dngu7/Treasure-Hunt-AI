#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Acknowledgement
# Resource: https://raw.githubusercontent.com/ichinaski/astar/master/pqueue.py
# - resource used are: PriorityQueue itself.
#---------------------------------------------------------------------------------------------------------------------------------------------------#


import heapq
import itertools


REMOVED = '<removed-task>'      # placeholder for a removed task

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# PriorityQueue Class Object
# Contains functions required to push and pop Queue but orgainizes according to 
# Priority
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class PriorityQueue:
    def __init__(self):
        self.pq = []                         # list of entries arranged in a heap
        self.entry_finder = {}               # mapping of tasks to entries
        self.counter = itertools.count()     # unique sequence count

    def __nonzero__(self):
        if self.entry_finder:
            return True
        return False

    #---------------------------------------------------#
    # priority
    # returning what prioiry it has for the key given.
    #---------------------------------------------------#
    def priority(self, task):
        if self.entry_finder.has_key(task):
            return self.entry_finder[task][0]
        return None
    
    #---------------------------------------------------#
    # push
    # push according to priority
    #---------------------------------------------------#
    def push(self, task, priority=0):
        'Add a new task or update the priority of an existing task'
        if task in self.entry_finder:
            self.remove_task(task)
        count = next(self.counter)
        entry = [priority, count, task]
        self.entry_finder[task] = entry
        heapq.heappush(self.pq, entry)

    #---------------------------------------------------#
    # remove_task
    # Mark an existing task as REMOVED.  Raise KeyError if not found.
    #---------------------------------------------------#
    def remove_task(self, task):
        'Mark an existing task as REMOVED.  Raise KeyError if not found.'
        entry = self.entry_finder.pop(task)
        entry[-1] = REMOVED


    #---------------------------------------------------#
    # pop
    # Removing the first element of Queue
    # Remove and return the lowest priority task. Raise KeyError if empty.
    #---------------------------------------------------#
    def pop(self):
        'Remove and return the lowest priority task. Raise KeyError if empty.'
        while self.pq:
            priority, count, task = heapq.heappop(self.pq)
            if task is not REMOVED:
                del self.entry_finder[task]
                return task, priority
        #raise KeyError('pop from an empty priority queue')
        return [[], []]

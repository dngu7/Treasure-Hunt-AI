# Treasure-Hunt-AI
Implementation of an AI agent to play a text-based adventure game.

The agent is considered to be stranded on a small group of islands, with a few trees and the ruins of some ancient buildings. It is required to move around a rectangular environment, collecting tools and avoiding (or removing) obstacles along the way.

The obstacles and tools within the environment are represented as follows:

Obstacles  Tools
T 	tree      	a 	axe
-	door	        k	key
~	water	        o	stepping stone
*	wall	        $	treasure

The agent will be represented by one of the characters ^, v, <  or  >, depending on which direction it is pointing. The agent is capable of the following instructions:

L   turn left
R   turn right
F   (try to) move forward
C   (try to) chop down a tree, using an axe
U   (try to) unlock a door, using an key

When it executes an L or R instruction, the agent remains in the same location and only its direction changes. When it executes an F instruction, the agent attempts to move a single step in whichever direction it is pointing. The F instruction will fail (have no effect) if there is a wall or tree directly in front of the agent.

When the agent moves to a location occupied by a tool, it automatically picks up the tool. The agent may use a C or U instruction to remove an obstacle immediately in front of it, if it is carrying the appropriate tool. A tree may be removed with a C (chop) instruction, if an axe is held. A door may be removed with a U (unlock) instruction, if a key is held.

If the agent is not holding a raft or a stepping stone and moves forward into the water, it will drown.

If the agent is holding a stepping stone and moves forward into the water, the stone will automatically be placed in the water and the agent can step onto it safely. When the agent steps away, the stone will appear as an upper-case O. The agent can step repeatedly on that stone, but the stone will stay where it is and can never be picked up again.

Whenever a tree is chopped, the tree automatically becomes a raft which the agent can use as a tool to move across the water. If the agent is not holding any stepping stones but is holding a raft when it steps forward into the water, the raft will automatically be deployed and the agent can move around on the water, using the raft. When the agent steps back onto the land (or a stepping stone), the raft it was using will sink and cannot be used again. The agent will need to chop down another tree in order to get a new raft.

If the agent attempts to move off the edge of the environment, it dies.

To win the game, the agent must pick up the treasure and then return to its initial location.

# Running as a Single Process #

javac *.java
java Step -i s0.in
You should then see something like this:
~~~~~~~~~~~~~~~~~~~~~~~~
~~********************~~
~~* a   *     T   o  *~~
~~* o *-*  v  **     *~~
~~****          *~~* *~~
~~ oT *    k     *  * ~~
~~*~~*           *~~  ~~
~~  $ ************    ~~
~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~

Enter Action(s): 
This allows you to play the role of the agent by typing commands at the keyboard (followed by <Enter>). Note:
a key can be used to open any door; once a door is opened, it has effectively been removed from the environment and can never be "closed" again.
an axe or key can be used multiple times, but each stone can be placed in the water only once.
C or U instructions will fail (have no effect) if the appropriate tool is not held, or if the location immediately in front of the agent does not contain an appropriate obstacle.

# Running in Network Mode #

Follow these instructions to see how the game runs in network mode:

open two windows, and cd to the src directory in both of them.
choose a port number between 1025 and 65535 - let's suppose you choose 31415.
type this in one window:
java Step -p 31415 -i s0.in
type this in the other window:
python3 Agent -p 31415

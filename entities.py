from functools import partial
import random

import numpy as np
# from fortress import Fortress
# from engine import Engine



class Entity:  

    #######     NODE ACTIONS     #######

    def __init__(self, fortress, char=None, filename=None, nodes=None, edges=None):
        self.char = char if char else '?'
        self.pos = [None, None]
        self.fortress = fortress  

        self.id = self.newID()   # generate a new ID for the entity
        
        self.cur_step = 0        # the current step the agent is on
        self.cur_node = 0        # the current node the agent is on
        self.moved_edge = None   # the edge that was activated when the node state changed
        self.other_ent = None    # the other entity that was involved in the edge activation
        self.possible_actions = fortress.node_types.copy()

        # get the random seed from the fortress and set it
        # seed = self.fortress.seed
        # random.seed(seed)

        # define the AI state graph
        self.nodes = []      # list of nodes; the index position corresponds to the node ID while the function name; saved as a string with the function name followed by any arguments with the value in parentheses
        self.edges = {}      # dictionary of node -> node activations; the key is the 2 node ID separated by a - and the value is the condition that activates the edge followed by any arguments with the value in parentheses
 
        # initalize a new behavior tree or import from a file
        if filename != None:
            self.importTree(filename)
        elif nodes != None and edges != None:
            self.nodes = nodes
            self.edges = edges
        else:
            self.makeTree(max_nodes_per_entity=len(fortress.node_types))

    # create a new id for the entity
    def newID(self,id_len=4):
        all_num = list(range(16**4))
        all_ids = self.fortress.entities.keys()
        while len(all_num) > 0:
            i = f'%{id_len}x' % random.choice(all_num)
            if i not in all_ids:
                return i
            all_num.remove(int(i,16))

        return f'%0{id_len}x' % random.randrange(16**(id_len+1))

    #######     NODE ACTIONS     #######

     # returns the nearest entity of a certain character (excluding itself)
    def _anotherEnt(self, entChar):
        return self.fortress.closestEnt(self.pos[0],self.pos[1],entChar,(self.id if entChar == self.char else None))
    

    # move to a random adjacent position if possible
    def _randAdjPos(self):
        # TODO: currently moves one tile at a tile in a random direction
        pos_mod = [[0,1], [0,-1], [1,0], [-1,0]]
        rpos = random.choice(pos_mod)
        new_pos = [self.pos[0] + rpos[0], self.pos[1] + rpos[1]]
        # self.fortress.addLog("Entity trying to move to " + str(new_pos))
        if self.fortress.validPos(new_pos[0], new_pos[1]):
            return new_pos
        return None
    

    # create another instance of the entity but with different id and position
    def clone(self,pos=None,transform=False):
        new_ent = Entity(self.fortress, self.char,nodes=self.nodes.copy(),edges=self.edges.copy())
        new_ent.id = self.newID()

        #new_ent.pos = pos if pos else self.fortress.randomPos()
        new_ent.pos = pos if pos else self._randAdjPos()

        # don't clone if the position is invalid or if something is already there
        if new_ent.pos == None or (not transform and self.fortress.entAtPos(new_ent.pos[0], new_ent.pos[1])):
            self.fortress.addLog("Clone failed")
            return None
        
        self.fortress.addEntity(new_ent)
        self.fortress.addLog(f"[{self.char}.{self.id}] cloned to [{new_ent.char}.{new_ent.id}] at {str(new_ent.pos)}")
        return new_ent

    # if entity dies, remove from map
    def die(self):
        self.fortress.addLog(f"[{self.char}.{self.id}] died")
        self.fortress.removeFromMap(self)
    
    # if entity takes another entity, remove from map
    def take(self, entityChar):
        # if self.other_ent:
            # self.fortress.addLog(f"[{self.char}.{self.id}] took [{self.other_ent.char}.{self.other_ent.id}]")
            # self.other_ent.die()
            # self.other_ent = None

        other_ent = self._anotherEnt(entityChar)
        if other_ent:
            self.fortress.addLog(f"[{self.char}.{self.id}] took [{other_ent.char}.{other_ent.id}]")
            other_ent.die()

   
    # if entity moves, update position
    def move(self):
        new_pos = self._randAdjPos()
        # self.fortress.addLog("Entity trying to move to " + str(new_pos))
        if new_pos:
            self.pos = new_pos
            self.fortress.addLog(f"[{self.char}.{self.id}] moved to {str(self.pos)}")

     # if entity moves and entity is not in the way, update position
    def wall(self, entityChar):
        new_pos = self._randAdjPos()
        # self.fortress.addLog("Entity trying to move to " + str(new_pos))
        if new_pos:
            eap = self.fortress.entAtPos(new_pos[0],new_pos[1])   # check if there's an entity at the position and if so, not the specified one
            if not eap or eap.char != entityChar:
                self.pos = new_pos
                self.fortress.addLog(f"[{self.char}.{self.id}] moved to {str(self.pos)}")
            else:
                self.fortress.addLog(f"[{self.char}.{self.id}] blocked by wall {eap.char}.{eap.id}")

    # moves the entity towards a particular entity on the map
    def chase(self, entityChar):

        # if not self.other_ent:
        #     return
        other_ent = self._anotherEnt(entityChar)
        if not other_ent:
            return

        # set the target position to the other entity's position
        # pos = self.other_ent.pos
        pos = other_ent.pos

        new_pos = self.pos.copy()
        dir = []

        if pos[0] > self.pos[0]:   # go east
            dir.append('east')
        elif pos[0] < self.pos[0]:  # go west
            dir.append('west')
        if pos[1] > self.pos[1]:    # go south
            dir.append('south')
        elif pos[1] < self.pos[1]:  # go north
            dir.append('north')

        if len(dir) == 0:
            return
        
        # randomly choose a direction to move from the directions need to go in
        rdir = random.choice(dir)
        if rdir == 'east':
            new_pos[0] += 1
        elif rdir == 'west':
            new_pos[0] -= 1
        elif rdir == 'south':
            new_pos[1] += 1
        elif rdir == 'north':
            new_pos[1] -= 1

        # check if the new position is valid
        if self.fortress.validPos(new_pos[0], new_pos[1]):
            self.pos = new_pos
            self.fortress.addLog(f"[{self.char}.{self.id}] moved to {str(self.pos)} goto {str(pos)}")

    # check if 2 positions are the same
    def _samePos(self, pos1, pos2):
        return pos1[0] == pos2[0] and pos1[1] == pos2[1]

    # if entity pushes another entity, move the other entity
    def push(self, entityChar):

        # if not self.other_ent:
        #     return
        other_ent = self._anotherEnt(entityChar)
        if not other_ent:
            return
            
        # get the next position over
        pos_mod = [[0,1], [0,-1], [1,0], [-1,0]]
        rpos = random.choice(pos_mod)
        new_pos = [self.pos[0] + rpos[0], self.pos[1] + rpos[1]]

        # check if the other entity is in the next position
        # if self._samePos(new_pos, self.other_ent.pos):
        #     # move the other entity in the same direction as the entity (if the previous position matched)
        #     new_pos_e = [self.other_ent.pos[0] + rpos[0], self.other_ent.pos[1] + rpos[1]]
        #     if self.fortress.validPos(new_pos_e[0], new_pos_e[1]):
        #         # move this entity
        #         self.pos = new_pos

        #         # move the other entity
        #         self.other_ent.pos = new_pos_e
        #         self.fortress.addLog(f"[{self.char}.{self.id}] pushed [{self.other_ent.char}.{self.other_ent.id}]")

        if self._samePos(new_pos, other_ent.pos):
            # move the other entity in the same direction as the entity (if the previous position matched)
            new_pos_e = [other_ent.pos[0] + rpos[0], other_ent.pos[1] + rpos[1]]
            if self.fortress.validPos(new_pos_e[0], new_pos_e[1]):
                # move this entity
                self.pos = new_pos

                # move the other entity
                other_ent.pos = new_pos_e
                self.fortress.addLog(f"[{self.char}.{self.id}] pushed [{other_ent.char}.{other_ent.id}]")

        elif self.fortress.validPos(new_pos[0], new_pos[1]):
            # move this entity
            self.pos = new_pos
            self.fortress.addLog(f"[{self.char}.{self.id}] moved to {str(self.pos)} - (not able to push)")

    # add another entity to the map
    def addEnt(self, entityChar):
        new_ent_def = self.fortress.CHARACTER_DICT[entityChar]
        adj_pos = self._randAdjPos()
        
        # check if the position is valid or if there is already an entity there
        if not adj_pos or self.fortress.entAtPos(adj_pos[0], adj_pos[1]):
            return
        
        new_ent = new_ent_def.clone(adj_pos)
        if new_ent:
            self.fortress.addEntity(new_ent)
            self.fortress.addLog(f"[{self.char}.{self.id}] added [{new_ent.char}.{new_ent.id}] at {str(new_ent.pos)}")

    # transform this entity into another entity
    def transform(self, entityChar):
        new_ent_def = self.fortress.CHARACTER_DICT[entityChar]
        new_ent = new_ent_def.clone(self.pos,True)
        if new_ent:
            self.fortress.addEntity(new_ent)
            self.fortress.addLog(f"[{self.char}.{self.id}] transformed into [{new_ent.char}.{new_ent.id}] at {str(new_ent.pos)}")
            self.die()


    # do nothing
    def noneAct(self):
        pass


    #######     EDGE CONDITIONS     #######


    # every x steps in the simulation
    def every_step(self, steps):
        steps = int(steps)
        if self.cur_step % steps == 0:
            return True
        return False
    
    # if entity touches another entity with the specified character
    def touch(self, entityChar):
        # self.fortress.addLog(f"[{self.char}.{self.id}] checking if touching [{entityChar}]")

        # currently returns true if the entity is touching another entity
        for i,ent in self.fortress.entities.items():
            # skip self
            if i == self.id:
                continue
            # check if the entity is touching another entity
            if ent.char == entityChar:
                if ent.pos[0] == self.pos[0] and ent.pos[1] == self.pos[1]:
                    self.other_ent = ent   # save the other entity that was touched
                    return True
        return False
    
    # if entity is within x spaces of another entity
    def within(self,entityChar,range):
        range = int(range)
        for i,ent in self.fortress.entities.items():
            # skip self
            if i == self.id:
                continue
            # check if the entity is touching another entity
            if ent.char == entityChar:
                if abs(ent.pos[0] - self.pos[0]) <= range and abs(ent.pos[1] - self.pos[1]) <= range:
                    self.other_ent = ent
                    return True
        return False
    
    # if entity is next to another entity
    def nextTo(self,entityChar):
        return self.within(entityChar,1)


    def noneCond(self):
        return True
        

    #######     GRAPH DEVELOPMENT     #######

    # return a new random node with the name and parameters provided
    def newNode(self):
        new_state = random.choice(self.possible_actions)
        self.possible_actions.remove(new_state)
        
        new_node = f"{new_state} "

        return new_node.strip()
    
    # return a new random edge with the condition and parameters provided
    def newEdge(self):
        new_edge = ""
        new_cond = random.choice(self.fortress.CONFIG['edge_conditions'])

        new_edge = f"{new_cond} "
        if EDGE_DICT[new_cond]['args'] != []:
            for arg in EDGE_DICT[new_cond]['args']:
                if arg == "entityChar":
                    new_edge += f"{random.choice(self.fortress.CONFIG['character'])} "
                elif arg == "steps":
                    new_edge += f"{random.randint(self.fortress.CONFIG['step_range'][0],self.fortress.CONFIG['step_range'][1])} "
                elif arg == "range":
                    new_edge += f"{random.randint(self.fortress.CONFIG['prox_range'][0],self.fortress.CONFIG['prox_range'][1])} "


        return new_edge.strip()


    # create a new FSM tree
    def makeTree(self, max_nodes_per_entity):

        # random.seed(self.fortress.seed+int(self.id,16))  # set the seed for the entity

        # add base idle node
        self.nodes.append("idle")

        # get the pdf of an inverse logarithmic distribution
        
        # create the nodes (must have at least 2)
        # num_nodes = random.randint(1, max_nodes_per_entity-1)
        idxs = np.arange(max_nodes_per_entity) + 1
        vals = (1 / idxs ) ** 2
        # Make the decrease even steeper
        vals = vals / np.sum(vals)
        num_nodes = np.random.choice(idxs, p=vals)
        # print(f"num_nodes: {num_nodes}")
        for i in range(num_nodes):
            self.nodes.append(self.newNode())

        # create edges based on the nodes
        for i in range(num_nodes*2):  #arbitrary number of edges (randomly assigned so some may get overwritten)
            node1 = random.randint(0, num_nodes)
            node2 = random.randint(0, num_nodes)

            edge = f"{node1}-{node2}"   # create the edge

            # add the condition
            self.edges[edge] = self.newEdge()

        # validate the tree
        self.connectOrphanNodes()


    # validate the tree
    def connectOrphanNodes(self):
        # add unconnected nodes
        right_nodes = list(set([e.split("-")[1] for e in self.edges.keys() if e.split("-")[0] != e.split("-")[1]]))
        for i in range(len(self.nodes)):
            if i not in right_nodes:
                other_nodes = list(range(len(self.nodes)))
                other_nodes.remove(i)
                new_edge_left = random.choice(other_nodes)
                ne = f"{new_edge_left}-{i}"
                self.edges[ne] = self.newEdge()
                right_nodes.append(i)

        # sort the edges by key
        self.edges = dict(sorted(self.edges.items()))

    # connect a single orphan node
    def connectAnnieNode(self, node_index):
        other_nodes = list(range(len(self.nodes)))
        other_nodes.remove(node_index)
        new_edge_left = random.choice(other_nodes)
        daddy_warbucks = f"{new_edge_left}-{node_index}" #>:)
        self.edges[daddy_warbucks] = self.newEdge()

        # sort the edges by key
        # print(self.edges.keys())
        self.edges = dict(sorted(self.edges.items()))


    # kill the orphan edges
    def killOrphanEdges(self, node_index):
        new_edges = {}

        # find the edges that are connected to the node
        for e in self.edges.keys():
            ls = int(e.split("-")[0])
            rs = int(e.split("-")[1])
            # if the edge is connected to the node, delete it
            if ls == node_index or rs == node_index:
                continue
            # if the edge has a value greater than the index, reduce it by 1
            else:
                if ls > node_index:
                    ls -= 1
                if rs > node_index:
                    rs -= 1
                new_edges[f"{ls}-{rs}"] = self.edges[e]

        # update the edges
        self.edges = new_edges


    # print the tree out in a nice format
    '''

        [CHARACTER SYMBOL]:
        -- NODES --
        [INDEX #]: [NAME] 
        -- EDGES --
        [INDEX #] - [INDEX #]: (FUNCTION CALL) (PARAMETERS)
    '''
    def printTree(self):
        outStr = ""

        # character symbol
        outStr += f"{self.char}:\n"

        # nodes
        outStr += "-- NODES --\n"
        for i in range(len(self.nodes)):
            outStr += f"{i}: {self.nodes[i]}\n"  # assume there are arguments provided with the node

        # edges
        outStr += "-- EDGES --\n"

        for key, action in self.edges.items():
            outStr += f"{key}: {action}\n"        

        return outStr


    # export the tree to a file
    def exportTree(self,filename):
        with open(filename, 'w+') as f:
            outstr = self.printTree()
            f.write(outstr)
            f.close()


    # import a tree from a file
    def importTree(self,filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines if line != "\n"]  # remove empty lines

            # parse the character
            self.char = lines[0].strip()[-1]

            # find the breaker headers
            node_break = lines.index("-- NODES --")
            edge_break = lines.index("-- EDGES --")

            # parse the nodes
            for i in range(node_break+1, edge_break):
                n = lines[i].split(": ")[1]
                self.nodes.append(n)

            # parse the edges
            for i in range(edge_break+1, len(lines)):
                e = lines[i].split(": ")
                self.edges[e[0]] = e[1]

            f.close()

    #######     UPDATES AND LOOPS    #######

    # update the behavior tree of the entity by looking at the graph and any connections
    def update(self):
        # increment the step counter
        self.cur_step += 1

        # do whatever is set at the current node first
        assert self.cur_node < len(self.nodes), (f"Current node {self.cur_node}"
                                                 f" is greater than the number of nodes {len(self.nodes)}")
        active_node = self.nodes[self.cur_node]
        act_node_parts = active_node.split(" ")

        # get the function to call
        func = act_node_parts[0]
        func = NODE_DICT[func]['func']  # could also use getattr(self, func)
        func = partial(func, self)

        # call the function with or without arguments
        if len(act_node_parts) > 1:
            args = act_node_parts[1:]
            func(*args)
        else:
            func()

        # if edges are available that fulfill the condition for crossing from the current node, then do it
        # order of priority: touch, nextTo, step, within, none

        # get all the edges that start at the current node
        edges = [key for key in self.edges.keys() if key.split("-")[0] == str(self.cur_node)]

        # sort the edges by priority
        # edges = sorted(edges, key=lambda x: EDGE_DICT[self.edges[x].split(" ")[0]]['priority'], reverse=True)
        
        # # check if any of the edges are valid
        # for edge in edges:
        #     # get the condition
        #     cond = self.edges[edge].split(" ")[0]
        #     cond = EDGE_DICT[cond]['func']
        #     cond = partial(cond, self)

        #     # get the arguments
        #     args = self.edges[edge].split(" ")[1:]

        #     # check if the condition is met
        #     if cond(*args):
        #         # get the node to transition to
        #         self.cur_node = int(edge.split("-")[1])
        #         self.moved_edge = edge
        #         break
        #     else:
        #         self.moved_edge = None


        ### FASTER EDGE CALCULATION ###

        # divide the edges into priority bins O(# edges @ cur_node)
        edge_prior = [[] for i in range(len(EDGE_DICT.keys()))]   # assume that the priorities are numerical 0-n
        for e in edges:
            edge_prior[EDGE_DICT[self.edges[e].split(" ")[0]]['priority']].append(e)

        # self.fortress.addLog(f"{self.char} -> {edge_prior}")

        # based on the bins enact the first possible priority - reversed order
        # worst case O(# edges @ cur_node) lower bound 1
        updated = False
        for i in range(len(edge_prior)-1,-1,-1):
            # finished updating
            if updated:
                break

            # self.fortress.addLog(f"{self.char}: {i} = {edge_prior[i]}")

            for edge in edge_prior[i]:
                # get the condition
                cond = self.edges[edge].split(" ")[0]
                cond = EDGE_DICT[cond]['func']
                cond = partial(cond, self)

                # get the arguments
                args = self.edges[edge].split(" ")[1:]

                # check if the condition is met
                if cond(*args):
                    # get the node to transition to
                    self.cur_node = int(edge.split("-")[1])
                    self.moved_edge = edge
                    updated = True
                    break   # end update
                else:
                    self.moved_edge = None

            




        # self.fortress.addLog(f"{self.char} is at node {self.cur_node}")

 
# associates names to the functions for the node actions the agent will perform
NODE_DICT = {
    "idle": {'func':Entity.noneAct, 'args':[]},
    "move": {'func':Entity.move, 'args':[]},
    "die": {'func':Entity.die, 'args':[]},
    "clone": {'func':Entity.clone, 'args':[]},
    "take": {'func':Entity.take, 'args':['entityChar']}, 
    "chase": {'func':Entity.chase, 'args':['entityChar']},
    "push": {'func':Entity.push, 'args':['entityChar']},
    "add": {'func':Entity.addEnt, 'args':['entityChar']},
    'transform': {'func':Entity.transform, 'args':['entityChar']},
    "move_wall":{'func':Entity.wall, 'args':['entityChar']}
}


# associates names to functions for the edge conditions that will activate the node actions
# lower number means it will happen last
EDGE_DICT = {
    "none": {'func':Entity.noneCond, 'args':[], 'priority':0},
    "step": {'func':Entity.every_step, 'args':['steps'], 'priority':1},
    "within": {'func':Entity.within, 'args':['entityChar','range'], 'priority':2},
    "nextTo": {'func':Entity.nextTo, 'args':['entityChar'], 'priority':3},
    "touch": {'func':Entity.touch, 'args':['entityChar'], 'priority':4}
}
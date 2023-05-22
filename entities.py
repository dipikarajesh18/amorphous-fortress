import random
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
        self.possible_actions = self.fortress.CONFIG['action_space'].copy()

        # get the random seed from the fortress and set it
        seed = self.fortress.seed
        random.seed(seed)

        # associates names to the functions for the node actions the agent will perform
        self.NODE_DICT = {
            "move": {'func':self.move, 'args':[]},
            "die": {'func':self.die, 'args':[]},
            "take": {'func':self.take, 'args':[]},  #only activated if other_ent is not None
            "idle": {'func':self.noneAct, 'args':[]}
        }

        # associates names to functions for the edge conditions that will activate the node actions
        self.EDGE_DICT = {
            "step": {'func':self.every_step, 'args':['steps'], 'priority':2},
            "touch": {'func':self.touch, 'args':['entityChar'], 'priority':1},
            "none": {'func':self.noneCond, 'args':[], 'priority':0}
        }

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
            self.makeTree()

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
    
    # create another instance of the entity but with different id and position
    def clone(self,pos=None):
        new_ent = Entity(self.fortress, self.char,nodes=self.nodes.copy(),edges=self.edges.copy())
        new_ent.id = self.newID()

        new_ent.pos = pos if pos else self.fortress.randomPos()
        # clone on top of the current entity if the position is invalid
        if new_ent.pos == None:
            new_ent.pos = self.pos
        
        self.fortress.addEntity(new_ent)
        return new_ent



    #######     NODE ACTIONS     #######


    # if entity dies, remove from map
    def die(self):
        self.fortress.addLog(f"[{self.char}.{self.id}] died")
        self.fortress.removeFromMap(self)
    
    # if entity takes another entity, remove from map
    def take(self):
        if self.other_ent:
            self.fortress.addLog(f"[{self.char}.{self.id}] took [{self.other_ent.char}.{self.other_ent.id}]")
            self.other_ent.die()
            self.other_ent = None
    
    # if entity moves, update position
    def move(self):
        # TODO: currently moves one tile at a tile in a random direction
        pos_mod = [[0,1], [0,-1], [1,0], [-1,0]]
        rpos = random.choice(pos_mod)
        new_pos = [self.pos[0] + rpos[0], self.pos[1] + rpos[1]]
        # self.fortress.addLog("Entity trying to move to " + str(new_pos))
        if self.fortress.validPos(new_pos[0], new_pos[1]):
            self.pos = new_pos
            self.fortress.addLog(f"[{self.char}.{self.id}] moved to {str(self.pos)}")

    # do nothing
    def noneAct(self):
        pass


    #######     EDGE CONDITIONS     #######


    # every x steps in the simulation
    def every_step(self, steps):
        steps = int(steps)
        if self.cur_step % steps == 0:
            self.cur_step = 0
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
    
    def noneCond(self):
        return True
        

    #######     GRAPH DEVELOPMENT     #######

    # return a new random node with the name and parameters provided
    def newNode(self):
        new_node = ""
        new_state = random.choice(self.possible_actions)
        self.possible_actions.remove(new_state)

        new_node = f"{new_state} "
        if self.NODE_DICT[new_state]['args'] != []:
            for arg in self.NODE_DICT[new_state]['args']:
                if arg == "entityChar":
                    new_node += f"? "   # use the entity passed in as an argument
        new_node = new_node.strip()
        return new_node
    
    # return a new random edge with the condition and parameters provided
    def newEdge(self,endNode):
        new_edge = ""
        new_cond = random.choice(self.fortress.CONFIG['edge_conditions'])

        new_edge = f"{new_cond} "
        if self.EDGE_DICT[new_cond]['args'] != []:
            for arg in self.EDGE_DICT[new_cond]['args']:
                if arg == "entityChar":
                    new_edge += f"{random.choice(self.fortress.CONFIG['character'])} "
                elif arg == "steps":
                    new_edge += f"{random.randint(self.fortress.CONFIG['step_range'][0],self.fortress.CONFIG['step_range'][1])} "

        return new_edge.strip()


    # create a new FSM tree
    def makeTree(self):

        random.seed(self.fortress.seed+int(self.id,16))  # set the seed for the entity

        # add base idle node
        self.nodes.append("idle")
        
        # create the nodes (must have at least 2)
        num_nodes = random.randint(1, len(self.possible_actions)-1)
        for i in range(num_nodes):
            self.nodes.append(self.newNode())

        # create edges based on the nodes
        for i in range(num_nodes*2):  #arbitrary number of edges (randomly assigned so some may get overwritten)
            node1 = random.randint(0, num_nodes)
            node2 = random.randint(0, num_nodes)

            edge = f"{node1}-{node2}"   # create the edge

            # add the condition
            self.edges[edge] = self.newEdge(node2)

        # sort the edges by key
        self.edges = dict(sorted(self.edges.items()))



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
        active_node = self.nodes[self.cur_node]
        act_node_parts = active_node.split(" ")

        # get the function to call
        func = act_node_parts[0]
        func = self.NODE_DICT[func]['func']  # could also use getattr(self, func)

        # call the function with or without arguments
        if len(act_node_parts) > 1:
            args = act_node_parts[1:]
            func(*args)
        else:
            func()

        # if edges are avaible that fulfill the condition for crossing from the current node, then do it
        # order of priority: every_step, touch, none

        # get all the edges that start at the current node
        edges = [key for key in self.edges.keys() if key.split("-")[0] == str(self.cur_node)]

        # sort the edges by priority
        edges = sorted(edges, key=lambda x: self.EDGE_DICT[self.edges[x].split(" ")[0]]['priority'], reverse=True)

        # check if any of the edges are valid
        for edge in edges:
            # get the condition
            cond = self.edges[edge].split(" ")[0]
            cond = self.EDGE_DICT[cond]['func']

            # get the arguments
            args = self.edges[edge].split(" ")[1:]

            # check if the condition is met
            if cond(*args):
                # get the node to transition to
                self.cur_node = int(edge.split("-")[1])
                self.moved_edge = edge
                break
            else:
                self.moved_edge = None

        # self.fortress.addLog(f"{self.char} is at node {self.cur_node}")





    

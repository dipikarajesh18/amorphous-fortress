import uuid
import random
from fortress import Fortress
from engine import Engine



class Entity:  
    def __init__(self, char, fortress):
        self.id = uuid.uuid4()
        self.char = char
        self.pos = [None, None]
        self.fortress = fortress          
        
        self.cur_step = 0

        # get the random seed from the fortress and set it
        seed = self.fortress.seed
        random.seed(seed)

        # associates names to the functions for the node actions the agent will perform
        self.NODE_DICT = {
            "move": {'func':self.move, 'args':[]},
            "die": {'func':self.die, 'args':[]},
            "take": {'func':self.take, 'args':['entityChar']},
            "none": {'func':self.noneAct, 'args':[]}
        }

        # associates names to functions for the edge conditions that will activate the node actions
        self.EDGE_DICT = {
            "step": {'func':self.every_step, 'args':['steps']},
            "touch": {'func':self.touch, 'args':['entityChar']},
            "none": {'func':self.noneCond, 'args':[]}
        }

        # define the AI state graph
        self.nodes = []      # list of nodes; the index position corresponds to the node ID while the function name; saved as a string with the function name followed by any arguments with the value in parentheses
        self.edges = {}      # dictionary of node -> node activations; the key is the 2 node ID separated by a - and the value is the condition that activates the edge followed by any arguments with the value in parentheses

        # initalize a new behavior tree
        self.makeTree()

    #######     NODE ACTIONS     #######


    # if entity dies, remove from map
    def die(self):
        self.fortress.removefromMap(self.id)
    
    # if entity takes another entity, remove from map
    def take(self, entityTaken):
        self.fortress.removefromMap(self.entiityTaken.id)
    
    # if entity moves, update position
    def move(self):
        # TODO: currently moves one tile at a tile in a random direction
        pos_mod = [[0,1], [0,-1], [1,0], [-1,0]]
        new_pos = random.choice(pos_mod) + self.pos
        if self.fortress.validPos(new_pos):
            self.pos = new_pos

    def noneAct(self):
        pass

    #######     EDGE CONDITIONS     #######

    def every_step(self, steps):
        if self.cur_step % steps == 0:
            return True
    
    def touch(self, entityChar):
        # currently returns true if the entity is touching another entity
        for ent in self.fortress.entities:
            if ent.char == entityChar:
                if ent.pos == self.pos:
                    return True
        return False
    
    def noneCond(self):
        pass
        

    ## Define graph stuff

    # return a new random node with the name and parameters provided
    def newNode(self):
        new_node = ""
        new_state = random.choice(self.fortress.CONFIG['action_space'])

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

        # add base idle node
        self.nodes.append("none")
        
        # create the nodes (must have at least 2)
        num_nodes = random.randint(2, 5)
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

    
    

# test out the entity class
if __name__ == "__main__":
    # create test engine, fortress, and entity
    testEngine = Engine()
    entTest = Entity("@", testEngine.fortress)
    print(f"SEED: {testEngine.fortress.seed}")
    print(entTest.printTree())

    

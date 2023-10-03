import numpy as np
import random
import re
from entities import NODE_DICT, Entity


# the environment where all of the simulation takes place
class Fortress():
    def __init__(self, config, width, height, borderChar='#',floorChar='.',seed=None):
        self.floor = floorChar
        self.border = borderChar
        self.width = width
        self.height = height
        self.max_entities = (width-2) * (height-2) * 2
        self.fortmap = []

        self.entities = {}   # dictionary of entities
        self.CHARACTER_DICT = {}    # definition of all of the characters classes in the simulation 
        self.CHAR_VISIT_TREE = {}   # stores the tree node visits of each entity instance per class
        self.max_aggregate_fsm_nodes = None   # the maximum number of nodes and edges over all entity types

        self.CONFIG = config  # a dictionary of values for configuration
        self.seed = random.randint(0,1000000) if seed == None else seed

        # random.seed(self.seed)
        # np.random.seed(self.seed)

        self.log = [f"============    FORTRESS SEED [{self.seed}]    =========", "Fortress initialized! - <0>"]
        self.steps = 0
        self.end_cause = "Code Interruption"

        # self.node_types = set()
        self.node_types = []
        for node in NODE_DICT:
            if NODE_DICT[node]['args'] == []:
                # self.node_types.add(node)
                self.node_types.append(node)
            elif NODE_DICT[node]['args'] == ['entityChar']:
                # [self.node_types.add(f"{node} {c}") for c in self.CONFIG['character']]
                self.node_types += [f"{node} {c}" for c in self.CONFIG['character']]


    # create a blank fortress
    def blankFortress(self):
        self.fortmap = np.full((self.height, self.width), self.floor)
        self.fortmap[0,:] = self.border
        self.fortmap[-1,:] = self.border
        self.fortmap[:,0] = self.border
        self.fortmap[:,-1] = self.border

    # print the fortress to the console
    def printFortress(self):
        for row in self.fortmap:
            print(''.join(row))


    # add an entity to the map
    def addEntity(self, ent):
        self.entities[ent.id] = ent

    # remove from the entity list and ID list based on the entity ID
    def removeFromMap(self, ent):
        if ent.id in self.entities:
            del self.entities[ent.id]


    # render the entities on the map
    def renderEntities(self,printMap=False):
        entMap = self.fortmap.copy()
        entDraw = list(self.entities.values())

        for ent in reversed(entDraw):
            x,y = ent.pos
            entMap[y,x] = ent.char
    
        # print to console
        if printMap:
            for row in entMap:
                print(''.join(row))

        return '\n'.join(([''.join(row) for row in entMap]))

    # check if a position is valid
    def validPos(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False

        if self.fortmap[y,x] == self.floor:
            return True
        else:
            return False
        
    # return a random position in the fortress
    def randomPos(self,inc_ent=True):
        all_pos = [(x,y) for x in range(1,self.width-1) for y in range(1,self.height-1)]
        random.shuffle(all_pos)
        for p in all_pos:
            x,y = p
            if self.validPos(x,y) and (not inc_ent or self.entAtPos(x,y) == None):
                return p
            
        # if no valid position is found
        return None
    
    # check if an entity is at a position
    def entAtPos(self, x, y):
        for ent in self.entities.values():
            if ent.pos[0] == x and ent.pos[1] == y:
                return ent
        return None
    
    # find the closest entity character from a specific position
    def closestEnt(self, x,y, c, eid=None):
        # find all of the characters (not including self)
        all_c = []
        for ent in self.entities.values():
            if ent.char == c and (eid == None or ent.id != eid):
                all_c.append(ent)

        # no entities left in the map
        if len(all_c) == 0:
            return None
        
        # calculate distances from all of the positions
        dist = {}
        for e in all_c:
            dist[e] = abs(e.pos[0]-x) + abs(e.pos[1]-y)
        
        # return entity with the smallest distance
        return sorted(dist.items(), key=lambda x:x[1])[0][0]
        



    # create new trees for every character in the config file
    def makeCharacters(self):
        n_ent_types = len(self.CONFIG['character'])
        n_node_types = len(self.node_types)
        self.max_nodes_per_type = len(self.node_types)
        self.max_aggregate_fsm_nodes = n_ent_types * n_node_types

        n_aggregate_nodes = random.randint(1, self.max_aggregate_fsm_nodes)
        # Randomly partition this number into a number of nodes per entity type
        n_nodes_per_ent_type = np.random.multinomial(n_aggregate_nodes, [1/n_ent_types]*n_ent_types, )

        self.CHARACTER_DICT = {}
        self.CHAR_VISIT_TREE = {}
        for i, c in enumerate(self.CONFIG['character']):
            # Hack it so that no nodes have empty or impossibly large FSMs. Sketchy, but it's ok because n_n
            n_nodes = min(max(n_nodes_per_ent_type[i], 1), self.max_nodes_per_type - 1)  # idle is already there by default
            ent = Entity(self,char=c, n_rand_nodes=n_nodes)
            ent.pos = [-1,-1]
            self.CHARACTER_DICT[c] = ent
            self.CHAR_VISIT_TREE[c] = {'nodes':set(),'edges':set()}

        self.addLog(f"{len(self.CHARACTER_DICT)} Unique character trees created")

    # def get_max_aggregate_fsm_nodes(self):
    #     n_ent_types = len(self.CHARACTER_DICT)
    #     nodes_per_ent_type = 0
    #     for node_dict in NODE_DICT.values():
    #         node_args = node_dict['args']
    #         if node_args == []:
    #             nodes_per_ent_type += 1
    #         elif node_args == ['entityChar']:
    #             nodes_per_ent_type += n_ent_types
    #     self.max_aggregate_fsm_nodes = nodes_per_ent_type * n_ent_types
    #     self.max_nodes_per_entity = nodes_per_ent_type
    #     return self.max_aggregate_fsm_nodes
        
    # check if the simulation should terminate
    def terminate(self):
        # if everything is dead
        if len(self.entities) == 0:
            self.end_cause = "Termination"
            return True
        return False
    
    # check if no activity has occurred in the fortress (based on the log information)
    def inactive(self):
        limit = self.CONFIG['inactive_limit']

        # check if over time from start
        if len(self.log) < 2 and self.steps > limit:
            return True

        # check if over time from last log
        last_log_time = re.match(r' -- <(\d+)>', self.log[-1])
        if (last_log_time) and (self.steps - int(last_log_time.groups()[0])) > limit:
            self.end_cause = "Inactivity"
            return True
        
        return False
    
    # check if too many entities in the simulation
    def overpop(self):
        if len(self.entities) > self.max_entities:
            self.end_cause = "Overpopulation"
            return True
        return False

        
    # adds a message to the log
    def addLog(self, txt):
        self.log.append(f"{txt} -- <{self.steps}>")

    # record the tree visits per entity and save it
    def addTreeVisit(self, ent):
        self.CHAR_VISIT_TREE[ent.char]['nodes'].add(ent.cur_node)
        if ent.moved_edge != None:
            self.CHAR_VISIT_TREE[ent.char]['edges'].add(ent.moved_edge)

    # reset the tree visits per entity
    def resetCharVisit(self):
        for c in self.CHAR_VISIT_TREE:
            self.CHAR_VISIT_TREE[c]['nodes'] = set()
            self.CHAR_VISIT_TREE[c]['edges'] = set()
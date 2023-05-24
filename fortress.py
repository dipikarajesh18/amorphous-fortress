import numpy as np
import random
import re
from entities import Entity

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

        self.CONFIG = config  # a dictionary of values for configuration
        self.seed = random.randint(0,1000000) if seed == None else seed

        random.seed(self.seed)
        np.random.seed(self.seed)

        self.log = [f"============    FORTRESS SEED [{self.seed}]    =========", "Fortress initialized! - <0>"]
        self.steps = 0
        self.end_cause = "Code Interruption"


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


    # create new trees for every character in the config file
    def makeCharacters(self):
        self.CHARACTER_DICT = {}
        for c in self.CONFIG['character']:
            ent = Entity(self,char=c)
            ent.pos = [-1,-1]
            self.CHARACTER_DICT[c] = ent

        self.addLog(f"{len(self.CHARACTER_DICT)} Unique character trees created")

        
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
        if (last_log_time) and (self.steps - int(last_log_time.group(1))) > limit:
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


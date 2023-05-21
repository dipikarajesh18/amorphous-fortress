import numpy as np
import random

# the environment where all of the simulation takes place
class Fortress():
    def __init__(self, config, width, height, borderChar='#',floorChar='.',seed=None):
        self.floor = floorChar
        self.border = borderChar
        self.width = width
        self.height = height
        self.fortmap = []

        self.entities = {}   # dictionary of entities

        self.CONFIG = config  # a dictionary of values for configuration
        self.seed = random.randint(0,1000000) if seed == None else seed

        self.log = ["Fortress initialized!"]


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
        del self.entities[ent.id]


    # render the entities on the map
    def renderEntities(self,printMap=False):
        entMap = self.fortmap.copy()
        for ent in self.entities.values():
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
        
        # DEBUG
        # self.addLog(f"\tValid position: {x},{y}?")
        # self.addLog(f"\tFortress: {self.width}x{self.height}")
        # self.addLog(f"\tFortress: {self.fortmap.shape}")

        if self.fortmap[y,x] == self.floor:
            return True
        else:
            return False
        
    # check if the simulation should terminate
    def terminate(self):
        # if everything is dead
        if len(self.entities) == 0:
            return True
        return False
        
    # adds a message to the log
    def addLog(self, txt):
        self.log.append(txt)


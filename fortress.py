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

        self.entities = []  #object list
        self.entIDs = []    #ID list
        self.entPos = []    #position list

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
        self.entities.append(ent)
        self.entIDs.append(ent.id)
        self.entPos.append(f"{ent.pos[0]},{ent.pos[1]}")

    # remove from the entity list and ID list based on the entity ID
    def removeFromMap(self, ent):
        ind = self.entIDs.index(ent.id)
        self.entities.pop(ind)
        self.entIDs.pop(ind)


    # render the entities on the map
    def renderEntities(self,printMap=False):
        entMap = self.fortmap.copy()
        for ent in self.entities:
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
        
    # update the position of an entity
    def updatePos(self, ent):
        ind = self.entIDs.index(ent.id)
        self.entPos[ind] = f"{ent.pos[0]},{ent.pos[1]}"

        # check if a position is occupied
        # return self.collision(ent)
    
    # check if an entity has# collided with another entity
    def collision(self, ent):
        entInd = self.entIDs.index(ent.id)

        collided_with = []
        for i in range(len(self.entIDs)):
            if i == entInd:
                continue
            if self.entPos[i] == self.entPos[entInd]:
                collided_with.append(self.entities[i])

        return collided_with
    
    # check if the simulation should terminate
    def terminate(self):
        # if everything is dead
        if len(self.entities) == 0:
            return True
        return False
        
    # adds a message to the log
    def addLog(self, txt):
        self.log.append(txt)


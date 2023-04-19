import uuid
import random

class Entity:  
    def __init__(self, char, fortress):
        self.id = uuid.uuid4()
        self.char = char
        self.pos = [None, None]
        self.fortress = fortress          
    
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
        
    
    

import random
import yaml
from fortress import Fortress
from entities import Entity
import numpy as np

class Engine():
    def __init__(self):

        # load the config file
        with open('alpha_config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

        # set the random seed
        self.seed = int(self.config['seed']) if self.config['seed'] and self.config['seed'] != 'any' else random.randint(0,1000000)
        random.seed(self.seed)
        np.random.seed(self.seed)
        # print(f"Seed: {self.seed}")

        # define the fortress
        self.fortress = Fortress(self.config,15,8,seed=self.seed)
        self.fortress.blankFortress()
        # self.fortress.printFortress()

        self.sim_tick = 0    # simulation tick

    # update the simulation entirely 
    def update(self):
        self.sim_tick += 1
        self.fortress.steps = self.sim_tick

        # update all of the entities
        cur_ents = list(self.fortress.entities.keys())

        # go through all of the living entities
        for k in cur_ents:
            # if still alive
            if k in self.fortress.entities:
                ent = self.fortress.entities[k]
                ent.update()

    # export the log to a file
    def exportLog(self,filename):
        with open(filename, 'w') as file:
            for line in self.fortress.log:
                file.write(line + '\n')


    # populate the fortress with entities
    def populateFortress(self):
        num_classes = random.randint(1,len(self.config['character']))  #only use a subset of the characters (1-all)
        rposx = np.random.randint(1,self.fortress.width-1,num_classes)
        rposy = np.random.randint(1,self.fortress.height-1,num_classes)

        char_left = self.config['character'].copy()

        for i in range(num_classes):

            c = random.choice(char_left)  # pick a random character
            ent = Entity(self.fortress, char=c)
            ent.pos = [rposx[i], rposy[i]]
            self.fortress.addEntity(ent)

            # have a chance to make copies of the same entity
            if random.random() < self.config['pop_chance']:
                ent.clone()

            char_left.remove(c) # remove the character from the list

        self.fortress.addLog("Fortress randomly populated") # add a log message

    
        

# test out the entity class
if __name__ == "__main__":
    # create test engine, fortress, and entity
    testEngine = Engine()
    # entTest = Entity(testEngine.fortress,"@")
    entTest = Entity(testEngine.fortress,filename="sample_entities/duck.txt")
    print(f"SEED: {testEngine.fortress.seed}")
    print(entTest.printTree())
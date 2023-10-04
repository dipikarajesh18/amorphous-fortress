import datetime
import random
import yaml

import numpy as np

from entities import Entity
from fortress import Fortress

class Engine():
    fortress: Fortress

    def __init__(self,config_file):

        # load the config file
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

        # set the random seed
        self.seed = int(self.config['seed']) if self.config['seed'] and self.config['seed'] != 'any' else random.randint(0,1000000)
        # random.seed(self.seed)
        # np.random.seed(self.seed)
        # print(f"Seed: {self.seed}")

        # define the fortress
        fort_w = int(self.config['width']) if 'width' in self.config else 15
        fort_h = int(self.config['height']) if 'height' in self.config else 8
        self.fortress = Fortress(self.config,fort_w,fort_h,seed=self.seed)
        self.fortress.blankFortress()
        self.fortress.addLog(f">>> CONFIG FILE: {config_file} <<<")
        self.fortress.addLog(f">>> TIME: {datetime.datetime.now()} <<<")
        # self.fortress.printFortress()

        self.sim_tick = 0    # simulation tick

        self.init_ent_str = ""    # string of all entities at the start of the simulation

    # update the simulation entirely 
    def update(self, tree_visits=False):
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
                if tree_visits:
                    self.fortress.addTreeVisit(ent)

    # export the log to a file
    def exportLog(self,filename):
        with open(filename, 'w') as file:
            for line in self.fortress.log:
                file.write(line + '\n')

    


    # populate the fortress with entities
    def populateFortress(self, init_strat='n_nodes', entropy_dict=None):
        # make every character
        self.fortress.makeCharacters(init_strat=init_strat, entropy_dict=entropy_dict)
        for c,e in self.fortress.CHARACTER_DICT.items():
            self.init_ent_str += f"{e.printTree()}\n"

        # populate the fortress with entities randomly
        map_size = self.fortress.width * self.fortress.height
        num_entities = random.randint(1,int(map_size*self.config['pop_perc']))    # number of entities to add

        rposx = np.random.randint(1,self.fortress.width-1,num_entities)
        rposy = np.random.randint(1,self.fortress.height-1,num_entities)

        for e in range(num_entities):
            c = random.choice(list(self.fortress.CHARACTER_DICT.keys()))
            ent = self.fortress.CHARACTER_DICT[c].clone([rposx[e], rposy[e]])
            if ent:
                self.fortress.addEntity(ent)

        self.recordState()   # record the initial state of the fortress
        self.fortress.addLog(f"Fortress randomly populated with {num_entities}")    # add a log message

    # Store the essential initial info in case we need to replicate/mutate the fortress later.
    def recordState(self):
        # These are backup/reference entities. They should never be added to the fortress lest they be modified in place.
        self.init_ents = []
        for e in self.fortress.entities.values():
            self.init_ents.append({'char':e.char, 'pos':e.pos})

    # reset the fortress to the initial state
    def resetFortress(self):
        # Remove all current entities
        self.fortress.entities = {}

        # reset the visits
        self.fortress.resetCharVisit()

        # Add the entities back in
        for e in self.init_ents:
            new_ent = self.fortress.CHARACTER_DICT[e['char']].clone(e['pos'])
            if new_ent:
                self.fortress.addEntity(new_ent)

        # reset the log
        self.fortress.log = [f"============    FORTRESS SEED [{self.seed}]    =========", "Fortress initialized! - <0>"]
        self.fortress.addLog(f">>> CONFIG FILE: {self.config} <<<")
        self.fortress.addLog(f">>> TIME: {datetime.datetime.now()} <<<")
        self.fortress.addLog(f"Fortress randomly populated with {len(self.init_ents)} entities")    # add a log message


        self.fortress.steps = 0




# test out the entity class
if __name__ == "__main__":
    # create test engine, fortress, and entity
    testEngine = Engine("CONFIGS/alpha_config.yaml")
    # entTest = Entity(testEngine.fortress,"@")
    entTest = Entity(testEngine.fortress,filename="ENT/duck.txt")
    print(f"SEED: {testEngine.fortress.seed}")
    print(entTest.printTree())
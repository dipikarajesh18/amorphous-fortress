import random
import yaml
from fortress import Fortress
class Engine():
    def __init__(self):

        # load the config file
        with open('alpha_config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

        # set the random seed
        self.seed = int(self.config['seed']) if self.config['seed'] and self.config['seed'] != 'any' else random.randint(0,1000000)
        random.seed(self.seed)
        print(f"Seed: {self.seed}")

        # define the fortress
        self.fortress = Fortress(self.config,15,8,seed=self.seed)
        self.fortress.blankFortress()
        # self.fortress.printFortress()

        self.sim_tick = 0    # simulation tick

    # update the simulation entirely 
    def update(self):
        self.sim_tick += 1

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

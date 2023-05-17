import random
import yaml
from fortress import Fortress
class Engine():
    def __init__(self,seed=None):

        # load the config file
        with open('alpha_config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        # set the random seed
        self.seed = seed if seed else random.randint(0,1000000)
        random.seed(self.seed)

        # define the fortress
        self.fortress = Fortress(config,15,8,seed=self.seed)
        self.fortress.blankFortress()
        self.fortress.printFortress()

        self.sim_tick = 0    # simulation tick

        

    # run the simulation
    def run(self):
        self.sim_tick = 0

        while not self.fortress.terminate():
            self.fortress.renderEntities()
            for ent in self.fortress.entities:
                ent.update(self.fortress)
                self.fortress.updatePos(ent)
                if self.fortress.terminate():
                    break


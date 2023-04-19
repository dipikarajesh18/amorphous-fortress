import random
class Engine():
    def __init__(self,seed=None):

        # define the fortress
        self.fortress = Fortress(15,8)
        self.fortress.blankFortress()
        self.fortress.printFortress()

        self.sim_tick = 0    # simulation tick

        # set the random seed
        self.seed = seed if seed else random.randint(0,1000000)
        random.seed(self.seed)


    def run(self):
        self.sim_tick = 0

        while not self.fortress.terminate():
            self.fortress.renderEntities()
            for ent in self.fortress.entities:
                ent.update(self.fortress)
                self.fortress.updatePos(ent)
                if self.fortress.terminate():
                    break
"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import copy
import curses
import random
import sys

import argparse
import numpy as np

from engine import Engine
from entities import Entity
from main import curses_render_loop, init_screens
from utils import newID

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

class EvoIndividual():
    n_sim_steps = 0

    def __init__(self, config_file: str, render: bool = False):
        self.config_file = config_file
        self.score = None
        engine = Engine(config_file)
        self.engine = engine
        self.render = render

    def clone(self):
        """Clone the individual."""

        # # FIXME: Why does this not work? Lots of empty maps...?
        # clone = EvoIndividual(self.config_file, self.render)
        # clone.engine.ref_ents = copy.deepcopy(self.engine.ref_ents)
        # # This is weird. We generate a new base set of entities from which to clone when adding new ones. A very roundabout way of doing things.
        # # TODO: When adding new random entities in mutation, create the entity from scratch right there.
        # clone.engine.fortress.makeCharacters()
        # return clone

        # The sketchy way...
        return copy.deepcopy(self)

    def init_random_fortress(self):
        self.engine.populateFortress()

    def mutate(self):
        """Mutate the fortress."""
        i = random.randint(0, 1)
        if i == 0 and len(self.engine.ref_ents) > 0:
            # Remove a random entity
            ent_id = random.choice(list(self.engine.ref_ents.keys()))
            ent = self.engine.ref_ents[ent_id]
            del self.engine.ref_ents[ent_id]
            # print(f'Removed entity {ent_id}, char {ent.char}, at {ent.pos}')
        elif i == 1:
            # Add a random entity
            # c = random.choice(list(self.engine.fortress.CHARACTER_DICT.keys()))
            x, y = random.randint(0, self.engine.fortress.width - 1), random.randint(0, self.engine.fortress.height - 1)
            # ent: Entity = self.engine.fortress.CHARACTER_DICT[c].clone((x, y))

            c = random.choice(self.engine.fortress.CONFIG['character'])
            ent = Entity(self.engine.fortress,char=c)
            ent.pos = [x, y]

            if ent:
                # Make sure the entity's id doesn't conflict with an existing one
                ent.id = newID(all_ids=self.engine.ref_ents.keys())
                self.engine.ref_ents[ent.id] = ent
                # print(f'Added entity {ent.id}, char {ent.char}, at {ent.pos}')
            else:
                pass
                # print(f'Failed to add entity, char {c}, at {x}, {y}')

        self.score = None


    def simulate_fortress(self):
        """Reset and simulate the fortress."""
        self.engine.resetFortress()

        # if self.render:
        #     screen_set, screen_dims = init_screens()

        loops = 0
        while not (self.engine.fortress.terminate() or self.engine.fortress.inactive() or \
                   self.engine.fortress.overpop() or loops >= self.n_sim_steps):
            # print(self.engine.fortress.renderEntities())
            self.engine.update()
            # if self.render:
            #     curses_render_loop(screen_set, screen_dims, self.engine)
            # print(loops)
            loops+=1

        if self.render:
            curses.endwin()

        print(self.engine.fortress.renderEntities())
        self.score = compute_fortress_score_dummy(self.engine)


def compute_fortress_score_dummy(engine: Engine):
    """Compute the score of a fortress."""
    score = 0
    for ent in engine.fortress.entities.values():
        score += ent.char == 'M'
    return score


def evolve(config_file: str):
    # Create argparser with boolean flag for rendering
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--render", action="store_true", help="Render the simulation")
    args = parser.parse_args()

    best_ind = None
    best_score = -1

    ind = EvoIndividual(config_file, args.render)
    ind.init_random_fortress()

    while best_score < 100:

        for _ in range(3):
            ind.mutate()

        # print(f'Random number: {random.random()}')

        # end_state = None
        # while True:
        ind.simulate_fortress()
            # new_end_state = ind.engine.fortress.renderEntities()
            # if end_state is None:
            #     end_state = new_end_state
            # else:
            #     assert end_state == new_end_state

        # show cause of termination
        # END_CAUSE = engine.fortress.end_cause
        # engine.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")
        # engine.fortress.log.append(f"\n{engine.init_ent_str}")

        if ind.score > best_score:
            print('New best score!')
            best_score = ind.score
            best_ind = ind
        
        print(f'Current fortress score: {ind.score}')
        print(f'Best fortress score: {best_score}')

        ind = best_ind.clone()


if __name__ == '__main__':
    conf_file = "CONFIGS/beta_config.yaml"
    evolve(conf_file)
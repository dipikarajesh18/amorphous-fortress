"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import curses
import random
import sys

import argparse
import numpy as np

from engine import Engine
from main import curses_render_loop, init_screens

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

def compute_fortress_score_dummy(engine):
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

    best_fort = None
    best_score = -1

    while best_score < 100:

        # setup the engine
        engine = Engine(config_file)
        np.random.seed(engine.seed)
        print('Seed:', engine.seed)
        random.seed(engine.seed)
        engine.populateFortress()

        if args.render:
            screen_set, screen_dims = init_screens()

        loops = 0
        while not (engine.fortress.terminate() or engine.fortress.inactive() or engine.fortress.overpop() or loops >= 100) :
            # print(engine.fortress.renderEntities())
            engine.update()
            if args.render:
                curses_render_loop(screen_set, screen_dims, engine)
            # print(loops)
            loops+=1

        # show cause of termination
        # END_CAUSE = engine.fortress.end_cause
        # engine.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")
        # engine.fortress.log.append(f"\n{engine.init_ent_str}")

        # End the simulation
        if args.render:
            curses.endwin()

        print(engine.fortress.renderEntities())
        score = compute_fortress_score_dummy(engine)

        if score > best_score:
            print('New best score!')
            best_score = score
            best_fort = engine.fortress

        print(f'Current fortress score: {score}')
        print(f'Best fortress score: {best_score}')


if __name__ == '__main__':
    conf_file = "CONFIGS/beta_config.yaml"
    evolve(conf_file)
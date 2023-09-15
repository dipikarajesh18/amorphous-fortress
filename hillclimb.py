"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import copy
import curses
import random
import math
import pickle
import cProfile
import matplotlib.pyplot as plt

import argparse
import numpy as np

from engine import Engine
from entities import Entity
from evo_utils import EvoIndividual
# from main import curses_render_loop, init_screens, DEBUG
from utils import newID

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

# Create argparser with boolean flag for rendering
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", type=str, default="CONFIGS/beta_config.yaml", help='Path to config file')
parser.add_argument("-r", "--render", action="store_true", help="Render the simulation")
parser.add_argument("-g", "--generations", type=int, default=1000, help='Number of generations to evolve for')
parser.add_argument("-e", "--edge_coin", type=float, default=0.5, help='Probability of mutating an edge')
parser.add_argument("-n", "--node_coin", type=float, default=0.5, help='Probability of mutating an node')
parser.add_argument("-i", "--instance_coin", type=float, default=0.5, help='Probability of adding or removing an entity instance')
parser.add_argument("-a", "--alife_exp", action="store_true", help="Running the alife experiment")


def hillclimb(config_file: str):
    global parser
    args = parser.parse_args()

    best_ind = None
    best_score = -math.inf

    ind = EvoIndividual(config_file, args.render)
    ind.init_random_fortress()

    generation = 0

    best_score_history = []
    cur_score_history = []
    entity_num_history = []

    # while best_score < ind.max_score:
    while generation < args.generations:

        # mutate randomly
        edge_rando = random.random()
        node_rando = random.random()
        instance_rando = random.random()

        while edge_rando < args.edge_coin:
            ind.mutateFSMEdges()
            edge_rando = random.random()
        
        while node_rando < args.node_coin:
            ind.mutateFSMNodes()
            node_rando = random.random()

        while instance_rando < args.instance_coin:
            ind.mutateEnt()
            instance_rando = random.random()

        ind.simulate_fortress(generation)

        if ind.score >= best_score:
            print(f'+++ New best score! {ind.score} - generation = {generation} +++')

            if ind.fitness_type == "M":
                print("=====   M   ======")
                print(ind.engine.fortress.CHARACTER_DICT['M'].printTree())
                print("")

            best_score = ind.score
            best_ind = ind.clone()
        
        # print the stats of the generation
        print(f"[ GENERATION {generation} ]")
        print(f'> Current fortress score: {ind.score}')
        print(f'> Best fortress score: {best_score}')
        print(f"> Total entities: {len(ind.engine.fortress.entities)}")
        print("")

        # add to the histories
        best_score_history.append(best_score)
        cur_score_history.append(ind.score)
        entity_num_history.append(len(ind.engine.fortress.entities))


        ind = best_ind.clone()
        generation+=1


    print("=================    SIMULATION COMPLETE   ==================")

    # when the experiment is finished export the log witht the trees
    best_ind.engine.init_ent_str = ""
    for c,e in best_ind.engine.fortress.CHARACTER_DICT.items():
        best_ind.engine.init_ent_str += f"{e.printTree()}\n"
    
    best_ind.engine.fortress.log.append(f"========================        EXPERIMENT COMPLETE [ GENERATIONS:{generation} - FINAL SCORE {best_score} ]     ========================\n")
    
    # add the coin flip probabilities
    best_ind.engine.fortress.log.append(f"\n++++  COIN FLIP PROBABILITIES  ++++\n")
    best_ind.engine.fortress.log.append(f"\nEdge: {args.edge_coin}\nNode: {args.node_coin}\nInstance: {args.instance_coin}\n")

    # add the initial map output
    best_ind.engine.fortress.log.append(f"\n++++  INITIAL MAP  ++++\n")
    best_ind.engine.fortress.log.append(f"\n{best_ind.init_fortress_str}")

    # add the final map output
    best_ind.engine.fortress.log.append(f"\n++++  FINAL MAP  ++++\n")
    best_ind.engine.fortress.log.append(f"\n{best_ind.engine.fortress.renderEntities()}")

    # add the character tree definitions
    best_ind.engine.fortress.log.append(f"\n++++  CHARACTER DEFINITIONS  ++++\n")
    best_ind.engine.fortress.log.append(f"\n{best_ind.engine.init_ent_str}")

    # add the tree coverage
    best_ind.engine.fortress.log.append(f"\n++++  TREE COVERAGE  ++++\n")
    for c, k in best_ind.engine.fortress.CHAR_VISIT_TREE.items():
        best_ind.engine.fortress.log.append(f"\n{c}")
        ent = best_ind.engine.fortress.CHARACTER_DICT[c]

        prob_n = len(k['nodes'])/len(ent.nodes) if len(ent.nodes) > 0 else 0
        prob_e = len(k['edges'])/len(ent.edges) if len(ent.edges) > 0 else 0

        best_ind.engine.fortress.log.append(f"Nodes: {len(k['nodes'])} / {len(ent.nodes)} = {prob_n:.2f}")
        best_ind.engine.fortress.log.append(f"Edges: {len(k['edges'])} / {len(ent.edges)} = {prob_e:.2f}")

    
    #####      NON ALIFE EXPERIMENT      #####

    if not args.alife_exp:
        # export the log
        best_ind.engine.exportLog(f"LOGS/hillclimber_{best_ind.fitness_type}_[{best_ind.engine.seed}].txt")

        # export the evo individual as a pickle
        best_ind.expEvoInd(f"EVO_IND/hillclimber_{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")

        # export the histories to a matplotlib graph
        plt.figure(figsize=(15,10))
        plt.plot(best_score_history, label="Best Score", color="red")
        plt.plot(cur_score_history, label="Current Score", color="orange")
        plt.plot(entity_num_history, label="Entity Count", color="green")
        plt.legend()
        plt.savefig(f"EVO_FIT/hillclimber_{best_ind.fitness_type}_[n-{args.node_coin},e-{args.edge_coin},i-{args.instance_coin}]_s[{best_ind.engine.seed}].png")


    #####      ALIFE EXPERIMENT      #####

    else:
        # export the log
        best_ind.engine.exportLog(best_ind.engine.config['log_file'])

        # export the evo individual as a pickle
        best_ind.expEvoInd(f"ALIFE_EXP/_pickle/hillclimber_{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")

        # export the histories to numpy array file
        np.save(f"ALIFE_EXP/_history/history_s[{best_ind.engine.seed}].npy", np.array([best_score_history, cur_score_history, entity_num_history]))

        

if __name__ == '__main__':
    # Create argparser with boolean flag for rendering
    sub_args = parser.parse_args()
    hillclimb(sub_args.config)
    # cProfile.run("evolve(conf_file)")
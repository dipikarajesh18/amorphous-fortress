"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import copy
import curses
import random
import math
import pickle
import cProfile
from typing import List
import matplotlib.pyplot as plt

import argparse
import numpy as np

from engine import Engine
from entities import Entity
from evo_utils import mutate_and_eval_ind
from hillclimb import EvoIndividual
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
parser.add_argument("-p", "--pop_size", type=int, default=10, help="Population size")
parser.add_argument("-xb", "--x_bins", type=int, default=100, help="Number of bins for x axis")
parser.add_argument("-yb", "--y_bins", type=int, default=100, help="Number of bins for y axis")


def get_xy_from_bcs(bc: tuple, bc_bounds: tuple, x_bins: int, y_bins: int):
    x = int((bc[0] - bc_bounds[0][0]) / (bc_bounds[0][1] - bc_bounds[0][0]) * x_bins)
    y = int((bc[1] - bc_bounds[1][0]) / (bc_bounds[1][1] - bc_bounds[1][0]) * y_bins)
    return (x, y)


def illuminate(config_file: str):
    global parser
    args = parser.parse_args()

    best_ind = None
    best_score = -math.inf

    mutants: List[EvoIndividual]
    mutants = [EvoIndividual(config_file, args.render) for _ in range(args.pop_size)]
    [ind.init_random_fortress() for ind in mutants]
    [ind.simulate_fortress(generation=0) for ind in mutants]
    mutant_scores = [ind.score for ind in mutants]
    mutant_bcs = [ind.get_bcs() for ind in mutants]
    bc_bounds = mutants[0].get_bc_bounds()
    mutant_xys = [get_xy_from_bcs(bc, bc_bounds, args.x_bins, args.y_bins) for bc in mutant_bcs]

    bc_0_ticks = np.linspace(bc_bounds[0][0], bc_bounds[0][1], args.x_bins)
    bc_1_ticks = np.linspace(bc_bounds[1][0], bc_bounds[1][1], args.y_bins)

    archive = np.full((args.x_bins, args.y_bins), None)
    fits = np.full((args.x_bins, args.y_bins), np.nan)

    # Sort by fitness (descending)
    # offspring = sorted(offspring, key=lambda ind: ind.score, reverse=True)
    # scores = [ind.score for ind in offspring]
    # bes_ind = offspring[0]
    # best_score = scores[0]
    # print(f"Initial population sorted by fitness: {[score for score in scores]}")

    generation = 0

    best_score_history = []
    cur_score_history = []
    entity_num_history = []


    # while best_score < ind.max_score:
    while generation < args.generations:
        
        if generation > 0:
            # Select `po_size` individuals from the population
            nonempty_cells  = np.argwhere(archive != None)
            parent_xys = random.choices(nonempty_cells, k=args.pop_size)
            mutants = [archive[xy[0], xy[1]].clone() for xy in parent_xys]
            [ind.simulate_fortress(generation=generation) for ind in mutants]
            mutant_scores = [ind.score for ind in mutants]
            mutant_xys = [get_xy_from_bcs(ind.get_bcs(), bc_bounds, args.x_bins, args.y_bins) for ind in mutants]


        for i, ind_i in enumerate(mutants):
            score_i = ind_i.score
            xy_i = mutant_xys[i]
            incumbent = archive[xy_i]
            if incumbent is None or score_i > incumbent.score:
                archive[xy_i] = ind_i
                fits[xy_i] = score_i
                print(f"Added mutant {i} to the archive at {xy_i}, with score {score_i}")
                if score_i > best_score:
                    best_score = score_i
                    best_ind = ind_i
        
        # print the stats of the generation
        print(f"[ GENERATION {generation} ]")
        print(f'> Best fortress score: {best_score}')
        # print(f"> Total entities: {len(best_ind.engine.fortress.entities)}")
        print(f'> Archive size: {len(np.argwhere(archive != None))}')
        print(f"> QD score: {np.nansum(fits)}")
        print("")

        # add to the histories
        best_score_history.append(best_score)
        cur_score_history.append(best_ind.score)
        entity_num_history.append(len(best_ind.engine.fortress.entities))

        if generation % 1 == 0:
            # Plot a heatmap of the archive
            plt.figure(figsize=(15,10))
            plt.imshow(fits, cmap='cool', interpolation='nearest')
            # Add x and y labels
            plt.xlabel('x') 
            plt.xticks(np.arange(args.x_bins // 10) * 10, [f"{bc_0_ticks[i] * 10:.2f}" for i in range(args.x_bins // 10)])
            plt.ylabel('y')
            plt.yticks(np.arange(args.y_bins // 10) * 10, [f"{bc_1_ticks[i] * 10:.2f}" for i in range(args.y_bins // 10)])
            plt.savefig(f"ALIFE_EXP/heatmap_gen-{generation}.png")

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
    illuminate(sub_args.config)
    # cProfile.run("evolve(conf_file)")
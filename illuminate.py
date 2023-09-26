"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import argparse
import copy
import curses
import os
import random
import math
import pickle
import shutil
from timeit import default_timer as timer
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from ray.util.multiprocessing import Pool
from tensorboardX import SummaryWriter

from evo_utils import EvoIndividual
from utils import get_bin_idx

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
parser.add_argument("-cf", "--checkpoint_frequency", type=int, default=10, help="Number of generations between checkpoints")
parser.add_argument("-pf", "--plot_frequency", type=int, default=10, help="Number of generations between plots")
parser.add_argument("-s", "--seed", type=int, default=0, help="Random seed for the experiment")
parser.add_argument("-ev", "--evaluate", action="store_true", help="Evaluate the archive")
parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing experiment directory")
parser.add_argument("-pr", "--percent_random", type=float, default=0.1, help="Percent of random individuals to add to the population")
parser.add_argument("-ft", "--fitness_type", type=str, default="tree", help="Fitness type: 'tree' or 'M'")
parser.add_argument("-bcs", "--bcs", type=str, nargs="+", default=['n_entities', 'n_nodes'], help="Behavior characteristics to use for evaluation")
parser.add_argument("-np", "--n_proc", type=int, default=1, help="Number of processes to use for simulation")


def get_xy_from_bcs(bc: tuple, bc_bounds: tuple, x_bins: int, y_bins: int):
    x = get_bin_idx(bc[0], bc_bounds[0], x_bins)
    y = get_bin_idx(bc[1], bc_bounds[1], y_bins)
    return (x, y)

    
def evaluate(args, archive):
    valid_xys = np.argwhere(archive != None)
    # Get list of individuals in order of decreasing fitness
    valid_inds = [archive[xy[0], xy[1]] for xy in valid_xys]
    valid_inds = sorted(valid_inds, key=lambda ind: ind.score, reverse=True)
    ind: EvoIndividual
    # Iterate through the archive and simulate each fortress while rendering
    for ind in valid_inds:
        ind.render = True
        ind.simulate_fortress(show_prints=False, map_elites=True)


def illuminate(config_file: str):
    global parser
    args = parser.parse_args()

    # WARNING: Stopping & resuming evolution mid-run will break reproducibility. Runs that go straight-through should
    #   be reproducible though.
    np.random.seed(args.seed)
    random.seed(args.seed)

    best_ind = None
    best_score = -math.inf

    mutants: List[EvoIndividual]
    mutants = [EvoIndividual(config_file, fitness_type=args.fitness_type, bcs=args.bcs, render=args.render) for _ in range(args.pop_size)]

    exp_dir = os.path.join("saves", 
                           (f"ME_fit-{args.fitness_type}_bcs-{args.bcs[0]}-{args.bcs[1]}"
                            f"_n-{args.node_coin}_e-{args.edge_coin}_i-{args.instance_coin}"
                            f"_xb-{args.x_bins}_yb-{args.y_bins}"
                            f"_p-{args.pop_size}"
                            f"_pr-{args.percent_random}"
                            f"_s-{args.seed}"
                            ))
    tb_writer = SummaryWriter(log_dir=exp_dir)

    # Find any existing archive files
    archive_files = ([f for f in os.listdir(exp_dir) if f.startswith("archive_gen-")] 
                        if os.path.exists(exp_dir) else [])
    if len(archive_files) == 0 or args.overwrite:
        if os.path.exists(exp_dir):
            shutil.rmtree(exp_dir)
        os.makedirs(exp_dir)
        generation = 0

        show_prints = generation % 25 == 0

        # TODO: Encode each fortress as some set (e.g. jax PyTree) of arrays.
        archive = np.full((args.x_bins, args.y_bins), None, dtype=object)
        fits = np.full((args.x_bins, args.y_bins), np.nan)

    else:
        # Get the latest archive
        latest_archive_file = max(archive_files, key=lambda f: int(f.split("-")[1].split(".")[0]))
        # Load it
        with open(os.path.join(exp_dir, latest_archive_file), 'rb') as f:
            archive = pickle.load(f)
        fits = np.full((args.x_bins, args.y_bins), np.nan)
        for xy in np.argwhere(archive != None):
            fits[xy[0], xy[1]] = archive[xy[0], xy[1]].score

        if args.evaluate:
            return evaluate(args, archive)

        # Get generation number
        generation = int(latest_archive_file.split("-")[1].split(".")[0])

        best_score = np.nanmax(fits)
        best_ind_xy = np.argwhere(fits == best_score)[0]
        best_ind = archive[best_ind_xy[0], best_ind_xy[1]]

    bc_bounds = mutants[0].get_bc_bounds()

    bc_1_ticks = np.linspace(bc_bounds[0][0], bc_bounds[0][1], args.x_bins)
    bc_0_ticks = np.linspace(bc_bounds[1][0], bc_bounds[1][1], args.y_bins)

    # Sort by fitness (descending)
    # offspring = sorted(offspring, key=lambda ind: ind.score, reverse=True)
    # scores = [ind.score for ind in offspring]
    # bes_ind = offspring[0]
    # best_score = scores[0]
    # print(f"Initial population sorted by fitness: {[score for score in scores]}")

    # best_score_history = []
    # entity_num_history = []

    if args.n_proc != 1:
        pool = Pool(processes=args.n_proc)

    # while best_score < ind.max_score:
    while generation < args.generations:
        gen_start_time = timer()
        
        if generation > 0:
            # Select `po_size` individuals from the population
            nonempty_cells  = np.argwhere(archive != None)
            n_rand_inds = int(args.pop_size * args.percent_random)
            n_parents = args.pop_size - n_rand_inds
            parent_xys = random.choices(nonempty_cells, k=n_parents)
            mutants = [archive[xy[0], xy[1]].clone() for xy in parent_xys]
            [m.mutate_ind(args) for m in mutants]
            rand_inds = [EvoIndividual(config_file, fitness_type=args.fitness_type, bcs=args.bcs, render=args.render) \
                            for _ in range(n_rand_inds)]
            mutants += rand_inds
            show_prints = generation % 25 == 0

        if args.n_proc == 1:
            [ind.simulate_fortress(show_prints=False, map_elites=True) for ind in mutants]
        else:
            # User ray to parallelize the simulation
            # Notice how the individuals in `mutants` aren't updated by this function. Why?
            rets = pool.map(lambda ind: ind.simulate_fortress(show_prints=False, map_elites=True), mutants)
            [ind.update(ret, map_elites=True) for ind, ret in zip(mutants, rets)]

        mutant_xys = [get_xy_from_bcs(ind.bc_sim_vals, bc_bounds, args.x_bins, args.y_bins) for ind in mutants]


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
        
        archive_size = len(np.argwhere(archive != None))
        qd_score = np.nansum(fits)
        # print the stats of the generation
        print(f"[ GENERATION {generation} ]")
        print(f'> Best fortress score: {best_score}')
        # print(f"> Total entities: {len(best_ind.engine.fortress.entities)}")
        print(f'> Archive size: {archive_size}')
        print(f"> QD score: {qd_score}")
        print(f"> Time elapsed: {timer() - gen_start_time:.2f} seconds")
        print("")

        tb_writer.add_scalar("qd_score", qd_score, generation)
        tb_writer.add_scalar("archive_size", archive_size, generation)
        tb_writer.add_scalar("best_score", best_score, generation)

        if args.fitness_type == "M":
            y_label, x_label = "n. entities", "n. @-type entities"
        else:
            y_label, x_label = args.bcs

        if generation % args.plot_frequency == 0:
            # Plot a heatmap of the archive
            # Calculate the aspect ratio based on x_bins and y_bins
            aspect_ratio = args.x_bins / args.y_bins

        plt.figure(figsize=(15,10))
        plt.imshow(fits, cmap='cool', interpolation='nearest', aspect='auto')  # Ensure that imshow respects aspect ratio setting of the axes

        # Add x and y labels
        plt.xlabel(x_label) 
        plt.ylabel(y_label)

        # Determine the scaling based on the size of x_bins and y_bins
        longest_bin = max(args.x_bins, args.y_bins)

        if args.x_bins < longest_bin:
            scale_factor_x = longest_bin / args.x_bins
        else:
            scale_factor_x = 1

        if args.y_bins < longest_bin:
            scale_factor_y = longest_bin / args.y_bins
        else:
            scale_factor_y = 1

        x_ticks = np.linspace(0, args.y_bins, 10)
        y_ticks = np.linspace(0, args.x_bins, 10)
        x_tick_vals = np.linspace(bc_bounds[1][0], bc_bounds[1][1], 10)
        y_tick_vals = np.linspace(bc_bounds[0][0], bc_bounds[0][1], 10)

        # Ensure axes have 1:1 aspect ratio
        plt.gca().set_aspect('equal', adjustable='box')

        # Set ticks
        plt.xticks(x_ticks, [f"{x:.2f}" for x in x_tick_vals])
        plt.yticks(y_ticks, [f"{y:.2f}" for y in y_tick_vals])

        # Add colorbar
        plt.colorbar()
        # plt.savefig(os.path.join(exp_dir, f"heatmap_gen-{generation}.svg"))
        plt.savefig(os.path.join(exp_dir, f"heatmap_gen-{generation}.png"))
        if generation % args.checkpoint_frequency == 0:
            # Save the archive as a pickle
            with open(os.path.join(exp_dir, f"archive_gen-{generation}.pkl"), 'wb') as f:
                pickle.dump(archive, f)
            if os.path.exists(os.path.join(exp_dir, f"archive_gen-{generation - args.checkpoint_frequency * 2}.pkl")):
                os.remove(os.path.join(exp_dir, f"archive_gen-{generation - args.checkpoint_frequency * 2}.pkl"))

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
        best_ind.engine.exportLog(f"LOGS/MAP-Elites_{best_ind.fitness_type}_[{best_ind.engine.seed}].txt")

        # export the evo individual as a pickle
        best_ind.expEvoInd(f"EVO_IND/MAP-Elites_{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")

        # export the histories to a matplotlib graph
        plt.figure(figsize=(15,10))
        # plt.plot(best_score_history, label="Best Score", color="red")
        # plt.plot(entity_num_history, label="Entity Count", color="green")
        plt.legend()
        plt.savefig(f"EVO_FIT/MAP-Elites_{best_ind.fitness_type}_[n-{args.node_coin},e-{args.edge_coin},i-{args.instance_coin}]_s[{best_ind.engine.seed}].png")


    #####      ALIFE EXPERIMENT      #####

    else:
        # export the log
        best_ind.engine.exportLog(best_ind.engine.config['log_file'])

        # export the evo individual as a pickle
        best_ind.expEvoInd(os.path.join(exp_dir, os.path.join(exp_dir, f"_pickle/{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")))

        # export the histories to numpy array file
        # np.save(os.path.join(exp_dir, f"_history/history_s[{best_ind.engine.seed}].npy"), np.array([best_score_history, entity_num_history]))

        

if __name__ == '__main__':
    # Create argparser with boolean flag for rendering
    sub_args = parser.parse_args()
    illuminate(sub_args.config)
    # cProfile.run("evolve(conf_file)")
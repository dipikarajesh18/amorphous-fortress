"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import argparse
import copy
import curses
import json
import os
import random
import math
import pickle
import shutil
from timeit import default_timer as timer
from typing import List
import hydra
import yaml

from config import EvoConfig
import matplotlib.pyplot as plt
import numpy as np
from ray.util.multiprocessing import Pool
from tensorboardX import SummaryWriter
from tqdm import tqdm
from entropy_utils import gen_entropy_dict

from evo_utils import EvoIndividual
from utils import get_bin_idx

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

# Create argparser with boolean flag for rendering
# parser = argparse.ArgumentParser()

def get_xy_from_bcs(bc: tuple, bc_bounds: tuple, x_bins: int, y_bins: int):
    x = get_bin_idx(bc[0], bc_bounds[0], x_bins)
    y = get_bin_idx(bc[1], bc_bounds[1], y_bins)
    return (x, y)

    
def enjoy(args, archive):
    valid_xys = np.argwhere(archive != None)
    # Get list of individuals in order of decreasing fitness
    valid_inds = [archive[tuple(xy)] for xy in valid_xys]
    ind: EvoIndividual
    # Iterate through the archive and simulate each fortress while rendering
    for ind in valid_inds:
        ind.render = True
        ind.simulate_fortress(
            show_prints=False, map_elites=True, n_new_sims=args.n_sims,
            n_steps_per_episode=args.n_steps_per_episode)
        breakpoint()


def eval_cheese(config: EvoConfig, archive, bc_bounds, exp_dir,
                n_steps_per_episode: int, cheese_name: str):
    """Iterate through all elites in an archive, evaluate them on new seeds, 
    and add them to a new archive. Note that we add results of new simulations
    to those of previous simulations (averaging evenly over all seeds)."""
    swiss_fits = np.full((config.x_bins, config.y_bins), np.nan)
    # Get list of individuals in order of decreasing fitness
    swiss_archive = np.empty_like(archive)
    ind_i: EvoIndividual
    # Iterate through the archive and simulate each fortress while rendering
    valid_xys = np.argwhere(archive != None)
    print(f"{len(valid_xys)} elites to evaluate.")

    # Shuffle the list to avoid having more/less computationally expensive
    # fortresses clustered at one end or the other (giving a false impression
    # of ETA). E.g. more entities generally more expensive to compute sim steps.
    np.random.shuffle(valid_xys)

    if config.n_proc != 1:
        pool = Pool(processes=config.n_proc)

    if config.n_proc == 1:
        # Use tqdm to show a progress bar
        for xy in tqdm(valid_xys, desc="Evaluating elites"):
        # for xy in valid_xys:
            xy = tuple(xy)
            ind_i = archive[xy]
            ind_i.simulate_fortress(
                show_prints=False, map_elites=True,
                n_new_sims=config.n_sims,
                n_steps_per_episode=n_steps_per_episode, verbose=False,
            )
    
    else:
        valid_inds = [archive[tuple(xy)] for xy in valid_xys]
        rets = list(tqdm(pool.imap(lambda ind: ind.simulate_fortress(
            show_prints=False, map_elites=True, n_new_sims=config.n_sims,
            n_steps_per_episode=config.n_steps_per_episode, verbose=False,
        ), valid_inds), desc="Evaluating elites"))
        [ind.update(ret, map_elites=True) for ind, ret in zip(valid_inds, rets)]
            
    for xy in valid_xys:
        ind_i = archive[tuple(xy)]
        xy_new = get_xy_from_bcs(ind_i.bc_sim_vals, bc_bounds, config.x_bins,
                                 config.y_bins)
        score_i = ind_i.score
        incumbent = swiss_archive[xy_new]
        if incumbent is None or score_i > incumbent.score:
            swiss_archive[xy_new] = ind_i
            swiss_fits[xy_new] = score_i
            print((f"Added mutant formerly at {xy} to the archive at {xy_new},"
                   f" with score {score_i}"))

    # Save the archive as a pickle
    with open(os.path.join(exp_dir, f"{cheese_name}_archive.pkl"), 'wb') as f:
        pickle.dump(swiss_archive, f)

    heatmap_filename = os.path.join(exp_dir, f"{cheese_name}_heatmap.png")
    plot_archive_heatmap(config, swiss_fits, bc_bounds=bc_bounds,
                         heatmap_filename=heatmap_filename)


def plot_archive_heatmap(config: EvoConfig, fits, bc_bounds, heatmap_filename,
                         cbar_label="% FSMs explored"):

    if config.fitness_type == "M":
        y_label, x_label = "n. entities", "n. @-type entities"
    else:
        y_label, x_label = config.bcs

    # Plot a heatmap of the archive
    # Calculate the aspect ratio based on x_bins and y_bins
    aspect_ratio = config.x_bins / config.y_bins

    plt.figure(figsize=(15,10))

    plt.imshow(fits, cmap='cool', interpolation='nearest', aspect='auto')

    # Add x and y labels
    plt.xlabel(x_label) 
    plt.ylabel(y_label)

    # Determine the scaling based on the size of x_bins and y_bins
    longest_bin = max(config.x_bins, config.y_bins)

    if config.x_bins < longest_bin:
        scale_factor_x = longest_bin / config.x_bins
    else:
        scale_factor_x = 1

    if config.y_bins < longest_bin:
        scale_factor_y = longest_bin / config.y_bins
    else:
        scale_factor_y = 1

    x_ticks = np.linspace(0, config.y_bins, 10)
    y_ticks = np.linspace(0, config.x_bins, 10)
    x_tick_vals = np.linspace(bc_bounds[1][0], bc_bounds[1][1], 10)
    y_tick_vals = np.linspace(bc_bounds[0][0], bc_bounds[0][1], 10)

    # Ensure axes have 1:1 aspect ratio
    plt.gca().set_aspect('equal', adjustable='box')

    # Set ticks
    plt.xticks(x_ticks, [f"{x:.2f}" for x in x_tick_vals])
    plt.yticks(y_ticks, [f"{y:.2f}" for y in y_tick_vals])

    # Add colorbar
    plt.colorbar(label=cbar_label)
    plt.tight_layout()
    # plt.savefig(os.path.join(exp_dir, f"heatmap_gen-{generation}.svg"))
    plt.savefig(heatmap_filename)


def get_exp_dir(config: EvoConfig):
    exp_dir = os.path.join("saves", 
                           (f"ME_fit-{config.fitness_type}"
                            f"_bcs-{config.bcs[0]}-{config.bcs[1]}"
                            f"_ss-{config.n_steps_per_episode}"
                            f"_n-{config.node_coin}_e-{config.edge_coin}"
                            f"_i-{config.instance_coin}"
                            f"_xb-{config.x_bins}_yb-{config.y_bins}"
                            f"_p-{config.pop_size}"
                            f"_pr-{config.percent_random}"
                            f"_s-{config.seed}"
                            ))
    return exp_dir


def get_archive_files(exp_dir: str):
    """Find any existing archive files."""
    archive_files = ([f for f in os.listdir(exp_dir) 
                      if f.startswith("archive_gen-")] 
                        if os.path.exists(exp_dir) else [])
    return archive_files


def load_latest_archive(exp_dir: str, archive_files: List[str]):
    # Get the latest archive
    archive_files = sorted(archive_files,
                           key=lambda f: int(f.split("-")[1].split(".")[0]))
    latest_archive_file = archive_files[-1]
    # Load it
    try:
        with open(os.path.join(exp_dir, latest_archive_file), 'rb') as f:
            archive = pickle.load(f)
    except EOFError:
        latest_archive_file = archive_files[-2]
        with open(os.path.join(exp_dir, latest_archive_file), 'rb') as f:
            archive = pickle.load(f)
    return archive


@hydra.main(version_base="1.3", config_path="conf", config_name="evolve")
def illuminate(config: EvoConfig):
    config_file: str = config.config_file
    # global parser

    # FIXME: Stopping & resuming evolution mid-run will break reproducibility.
    # Runs that go straight-through should be reproducible though.
    np.random.seed(config.seed)
    random.seed(config.seed)

    best_ind = None
    best_score = -math.inf

    if 'entropy' in config.bcs:
        if config.bcs.index('entropy') == 0:
            n_entropy_bins = config.x_bins
        else:
            n_entropy_bins = config.y_bins
        # Load config yaml
        config_file = os.path.join(config.config_file)
        config_file_dict = yaml.safe_load(open(config_file, 'r'))
        n_ent_types = len(config_file_dict['character'])


        entropy_dict = gen_entropy_dict(
            n_fsm_size_bins=n_ent_types, n_fsms=n_ent_types,
            n_entropy_bins=n_entropy_bins)
        init_strat = 'entropy'

    else:
        entropy_dict = None
        init_strat = 'n_nodes'

    mutants: List[EvoIndividual]
    dummy_ind = EvoIndividual(config_file, fitness_type=config.fitness_type,
                                bcs=config.bcs, render=config.render,
                                init_strat=init_strat, entropy_dict=entropy_dict,
                                init_seed=0)
    bc_bounds = dummy_ind.get_bc_bounds()
    exp_dir = get_exp_dir(config)

    tb_writer = SummaryWriter(log_dir=exp_dir)

    archive_files = get_archive_files(exp_dir)
    if len(archive_files) == 0 or config.overwrite:
        if os.path.exists(exp_dir):
            shutil.rmtree(exp_dir)
        os.makedirs(exp_dir)
        generation = 0

        show_prints = generation % 25 == 0
        rand_ind_seed_i = 0

        # TODO: Encode each fortress as some set (e.g. jax PyTree) of arrays.
        archive = np.full((config.x_bins, config.y_bins), None, dtype=object)
        fits = np.full((config.x_bins, config.y_bins), np.nan)

        mutants = [EvoIndividual(config_file, fitness_type=config.fitness_type, 
                                bcs=config.bcs, render=config.render,
                                init_strat=init_strat, entropy_dict=entropy_dict,
                                init_seed=rand_ind_seed_i+i)
                                for i in range(config.pop_size)]
        rand_ind_seed_i += config.pop_size

    else:
        archive_files = sorted(archive_files,
                            key=lambda f: int(f.split("-")[1].split(".")[0]))
        latest_archive_file = archive_files[-1]
        archive = load_latest_archive(exp_dir=exp_dir, archive_files=archive_files)
        stats = json.load(open(os.path.join(exp_dir, "stats.json"), "r"))
        rand_ind_seed_i = stats['rand_ind_seed_i']
        fits = np.full((config.x_bins, config.y_bins), np.nan)
        valid_xys = np.argwhere(archive != None)
        for xy in valid_xys:
            xy = tuple(xy)
            fits[xy] = archive[xy].score

        if config.enjoy:
            return enjoy(config, archive)

        if config.eval_swiss_cheese:
            return eval_cheese(config, archive, bc_bounds, exp_dir,
                               config.n_steps_per_episode, "swiss_cheese")

        if config.eval_cheesestring:
            return eval_cheese(config, archive, bc_bounds, exp_dir,
                               config.n_steps_per_episode * 5, "cheesestring")

        # Get generation number
        generation = int(latest_archive_file.split("-")[1].split(".")[0])

        best_score = np.nanmax(fits)
        best_ind_xy = np.argwhere(fits == best_score)[0]
        best_ind = archive[best_ind_xy[0], best_ind_xy[1]]

    bc_1_ticks = np.linspace(bc_bounds[0][0], bc_bounds[0][1], config.x_bins)
    bc_0_ticks = np.linspace(bc_bounds[1][0], bc_bounds[1][1], config.y_bins)

    # Sort by fitness (descending)
    # offspring = sorted(offspring, key=lambda ind: ind.score, reverse=True)
    # scores = [ind.score for ind in offspring]
    # bes_ind = offspring[0]
    # best_score = scores[0]
    # print(f"Initial population sorted by fitness: {[score for score in scores]}")

    # best_score_history = []
    # entity_num_history = []

    if config.n_proc != 1:
        pool = Pool(processes=config.n_proc)

    evo_start_time = timer()
    total_timesteps_since_reload = 0

    # while best_score < ind.max_score:
    while generation < config.generations:
        gen_start_time = timer()
        
        if generation > 0:
            # Select `po_size` individuals from the population
            nonempty_cells  = np.argwhere(archive != None)
            n_rand_inds = int(config.pop_size * config.percent_random)
            n_parents = config.pop_size - n_rand_inds
            parent_xys = random.choices(nonempty_cells, k=n_parents)
            mutants = [archive[xy[0], xy[1]].clone() for xy in parent_xys]
            [m.mutate_ind(config) for m in mutants]
            rand_inds = [EvoIndividual(
                config_file, fitness_type=config.fitness_type, bcs=config.bcs, 
                render=config.render, init_seed=rand_ind_seed_i+i) \
                            for i in range(n_rand_inds)]
            rand_ind_seed_i += n_rand_inds
            mutants += rand_inds
            # show_prints = generation % 25 == 0

        if config.n_proc == 1:
            [ind.simulate_fortress(
                show_prints=False, map_elites=True, n_new_sims=config.n_sims,
                n_steps_per_episode=config.n_steps_per_episode,
            ) for ind in mutants]
        else:
            # User ray to parallelize the simulation
            # Notice how the individuals in `mutants` aren't updated by this function. Why?
            rets = pool.map(lambda ind: ind.simulate_fortress(
                show_prints=False, map_elites=True, n_new_sims=config.n_sims,
                n_steps_per_episode=config.n_steps_per_episode,
            ), mutants)
            [ind.update(ret, map_elites=True) for ind, ret in zip(mutants, rets)]

        mutant_xys = [
            get_xy_from_bcs(
                ind.bc_sim_vals, bc_bounds, config.x_bins, config.y_bins
            ) 
                for ind in mutants]


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
        
        total_timesteps_since_reload += config.pop_size * (config.n_sims * config.n_steps_per_episode)
        archive_size = len(np.argwhere(archive != None))
        qd_score = np.nansum(fits)
        # print the stats of the generation
        print(f"[ GENERATION {generation} ]")
        print(f'> Best fortress score: {best_score}')
        # print(f"> Total entities: {len(best_ind.engine.fortress.entities)}")
        print(f'> Archive size: {archive_size}')
        print(f"> QD score: {qd_score}")
        print(f"> Time elapsed: {timer() - gen_start_time:.2f} seconds")
        print(f"> Running FPS: {total_timesteps_since_reload / (timer() - evo_start_time):.2f}")
        print("")

        tb_writer.add_scalar("qd_score", qd_score, generation)
        tb_writer.add_scalar("archive_size", archive_size, generation)
        tb_writer.add_scalar("best_score", best_score, generation)

        if generation % config.plot_frequency == 0:
            heatmap_filename = os.path.join(exp_dir, f"heatmap_gen-{generation}.png")
            plot_archive_heatmap(config, fits, bc_bounds, heatmap_filename)

        if generation % config.checkpoint_frequency == 0:
            # Save the archive as a pickle
            with open(os.path.join(exp_dir, f"archive_gen-{generation}.pkl"), 'wb') as f:
                pickle.dump(archive, f)
            # Save stats as a json
            stats = {
                'rand_ind_seed_i': rand_ind_seed_i,
            }
            stats_json_path = os.path.join(exp_dir, "stats.json")
            with open(stats_json_path, "w") as f:
                json.dump(stats, f)

            if os.path.exists(os.path.join(exp_dir, f"archive_gen-{generation - config.checkpoint_frequency * 2}.pkl")):
                os.remove(os.path.join(exp_dir, f"archive_gen-{generation - config.checkpoint_frequency * 2}.pkl"))

        generation+=1


    print("=================    SIMULATION COMPLETE   ==================")

    # when the experiment is finished export the log witht the trees
    best_ind.engine.init_ent_str = ""
    for c,e in best_ind.engine.fortress.CHARACTER_DICT.items():
        best_ind.engine.init_ent_str += f"{e.printTree()}\n"
    
    best_ind.engine.fortress.log.append(f"========================        EXPERIMENT COMPLETE [ GENERATIONS:{generation} - FINAL SCORE {best_score} ]     ========================\n")
    
    # add the coin flip probabilities
    best_ind.engine.fortress.log.append(f"\n++++  COIN FLIP PROBABILITIES  ++++\n")
    best_ind.engine.fortress.log.append(f"\nEdge: {config.edge_coin}\nNode: {config.node_coin}\nInstance: {config.instance_coin}\n")

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

    if not config.alife_exp:
        # export the log
        best_ind.engine.exportLog(f"LOGS/MAP-Elites_{best_ind.fitness_type}_[{best_ind.engine.seed}].txt")

        # export the evo individual as a pickle
        best_ind.expEvoInd(f"EVO_IND/MAP-Elites_{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")

        # export the histories to a matplotlib graph
        plt.figure(figsize=(15,10))
        # plt.plot(best_score_history, label="Best Score", color="red")
        # plt.plot(entity_num_history, label="Entity Count", color="green")
        plt.legend()
        plt.savefig(f"EVO_FIT/MAP-Elites_{best_ind.fitness_type}_[n-{config.node_coin},e-{config.edge_coin},i-{config.instance_coin}]_s[{best_ind.engine.seed}].png")


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
    # sub_args = parser.parse_args()
    # illuminate(sub_args.config)
    illuminate()
    # cProfile.run("evolve(conf_file)")
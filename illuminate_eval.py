"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import os
import pickle

from config import EvoConfig
import numpy as np
from ray.util.multiprocessing import Pool
from tqdm import tqdm

from evo_utils import EvoIndividual, bc_funcs
from utils import get_bin_idx, plot_archive_heatmap

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

# Create argparser with boolean flag for rendering
# parser = argparse.ArgumentParser()

def get_xy_from_bcs(bc: tuple, bc_bounds: tuple, x_bins: int, y_bins: int):
    x = get_bin_idx(bc[0], bc_bounds[0], x_bins)
    y = get_bin_idx(bc[1], bc_bounds[1], y_bins)
    return (x, y)


def enjoy_printout(args, archive, exp_dir):
    exp_frames_dir = os.path.join(exp_dir, "printouts")
    os.makedirs(exp_frames_dir, exist_ok=True)
    valid_xys = np.argwhere(archive != None)
    valid_inds = [archive[tuple(xy)] for xy in valid_xys]
    # Get the individual with highest fitness
    best_ind = max(valid_inds, key=lambda ind: ind.score)
    # Get the individuals with lowest/highest values in each bc
    l_ind = min(valid_inds, key=lambda ind: ind.bc_sim_vals[0])
    r_ind = max(valid_inds, key=lambda ind: ind.bc_sim_vals[0])
    t_ind = min(valid_inds, key=lambda ind: ind.bc_sim_vals[1])
    b_ind = max(valid_inds, key=lambda ind: ind.bc_sim_vals[1])
    # Get individuals on the top/bottom of the leftmost column
    # First, get index of leftmost nonempty column
    l_col = np.argwhere(np.any(archive != None, axis=1))[0][0]
    l_col_inds = archive[:, l_col]
    r_col = np.argwhere(np.any(archive != None, axis=1))[-1][0]
    r_col_inds = archive[:, r_col]
    # t_row = np.argwhere(np.any(archive != None, axis=0))[0][0]
    # t_row_inds = archive[t_row, :]
    # b_row = np.argwhere(np.any(archive != None, axis=0))[-1][0]
    # b_row_inds = archive[b_row, :]
    # Get the individuals on the top/bottom of the leftmost column
    nonempty_l_col_idxs = np.argwhere(l_col_inds != None).flatten()
    nonempty_r_col_idxs = np.argwhere(r_col_inds != None).flatten()
    tl_ind, bl_ind = l_col_inds[nonempty_l_col_idxs[0]],\
        l_col_inds[nonempty_l_col_idxs[-1]]
    tr_ind, br_ind = r_col_inds[nonempty_r_col_idxs[0]],\
        r_col_inds[nonempty_r_col_idxs[-1]]
    # Find an individual in the middle of the archive
    mid_x = archive.shape[0] // 2
    mid_y = archive.shape[1] // 2
    # TODO: Make this robust in case there is no individual here
    mid_ind = archive[mid_x, mid_y]

    special_inds = [best_ind, l_ind, r_ind, t_ind, b_ind, tl_ind, bl_ind, 
                    tr_ind, br_ind, mid_ind]

    ind: EvoIndividual
    # Iterate through the archive and simulate each fortress while rendering
    # for xy in valid_xys:
    for ind in special_inds:
        archive_xy = get_xy_from_bcs(ind.bc_sim_vals, ind.get_bc_bounds(),
                                        args.x_bins, args.y_bins)
        # ind = archive[tuple(xy)]
        frames = []
        frames.append("Reloading individual:")
        frames.append(f"xy = {archive_xy}")
        frames.append(f"BCs = {ind.bc_sim_vals}\n")
        scores = []
        bcs = []
        for i in range(5):
            frames.append(f"Sim seed: {i}")
            ind.engine.fortress.rng_sim = np.random.default_rng(i)
            ind.engine.resetFortress()
            frames.append(ind.engine.fortress.renderEntities())
            loops = 0
            while not (ind.engine.fortress.terminate() or ind.engine.fortress.inactive() or \
                    ind.engine.fortress.overpop() or loops >= args.n_steps_per_episode):
                # print(self.engine.fortress.renderEntities())
                ind.engine.update(True)
                loops += 1
            frames.append(f'step: {loops}')
            frames.append(ind.engine.fortress.renderEntities())

            ind.get_fsm_stats()
            score = ind.fsm_stats['prop_visited']
            scores.append(score)
            bc_0, bc_1 = ind.bc_funcs[0](), ind.bc_funcs[1]()
            bcs.append((bc_0, bc_1))
            frames.append(f"Score: {score}")
            frames.append(f"BCs: {bc_0}, {bc_1}")
            # Add some stats about the fsm and the final number of entities
            frames.append(f"Final number of entities: {len(ind.engine.fortress.entities)}")
            frames.append(f"Number of nodes: {ind.fsm_stats['n_nodes']}")
            frames.append(f"Entropy of FSM sizes: {ind.get_entropy()}")
        mean_score = np.mean(scores)
        mean_bcs = np.mean(bcs, axis=0)
        frames.append(f"Mean score: {mean_score}")
        frames.append(f"Mean BCs: {mean_bcs}")
        new_xy = get_xy_from_bcs(mean_bcs, ind.get_bc_bounds(),
                                    args.x_bins, args.y_bins)
        frames.append(f"New xy: {new_xy}")
        # Join frames with newlines
        frames = "\n".join(frames)
        # Save frames to text file named after x and y coordinates
        with open(os.path.join(exp_frames_dir, f"{archive_xy[0]}-{archive_xy[1]}.txt"), "w") as f:
            f.write(frames)

    
def enjoy(args, archive):
    valid_xys = np.argwhere(archive != None)
    # Get list of individuals in order of decreasing fitness
    valid_inds = [archive[tuple(xy)] for xy in valid_xys]
    ind: EvoIndividual
    # Iterate through the archive and simulate each fortress while rendering
    for ind in valid_inds:
        ind.render = True
        breakpoint()
        ind.simulate_fortress(
            show_prints=False, map_elites=True, n_new_sims=args.n_sims,
            n_steps_per_episode=args.n_steps_per_episode)
        breakpoint()


def eval_cheese(config: EvoConfig, archive, bc_bounds, exp_dir,
                n_steps_per_episode: int, cheese_name: str):
    """Iterate through all elites in an archive, evaluate them on new seeds, 
    and add them to a new archive. Note that we add results of new simulations
    to those of previous simulations (averaging evenly over all seeds)."""


    # FIXME: Remove this backward-compatibility hack.
    # Swapping BC funcs to the unbounded versions. (Which themselves are
    # backward-compatibility hacks)
    for ind in archive.flatten():
        if ind is None:
            continue
        if not hasattr(ind, 'instance_entropy'):
            ind.instance_entropy = 0
        ind.bc_funcs = [bc_funcs[k] for k in config.bcs]

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
                eval_instance_entropy=True,
            )
    
    else:
        valid_inds = [archive[tuple(xy)] for xy in valid_xys]
        rets = list(tqdm(pool.imap(lambda ind: ind.simulate_fortress(
            show_prints=False, map_elites=True, n_new_sims=config.n_sims,
            n_steps_per_episode=config.n_steps_per_episode, verbose=False,
            eval_instance_entropy=True,
        ), valid_inds), desc="Evaluating elites"))
        [ind.update(ret, map_elites=True, eval_instance_entropy=True)
         for ind, ret in zip(valid_inds, rets)]
            
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


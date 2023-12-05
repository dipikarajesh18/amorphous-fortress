import json
import os
import pickle

import hydra
import numpy as np

from config import EvoConfig
from evo_utils import EvoIndividual, bc_funcs
from illuminate import get_archive_files, get_exp_dir, load_latest_archive, plot_archive_heatmap


def ill_cross_eval(cfg: EvoConfig, sweep_configs, sweep_params):
    # Create a directory for the results of the cross-evaluation.
    eval_dir = (f"cross_evals/{cfg.sweep_name}_ss-{cfg.n_steps_per_episode}")
    eval_dir = eval_dir + "_swiss" if cfg.eval_swiss_cheese else eval_dir
    eval_dir = eval_dir + "_string" if cfg.eval_cheesestring else eval_dir
    os.makedirs(eval_dir, exist_ok=True)
    # NOTE: Assuming bcs are the same for all configs, and that archives have 
    #   the same dimensions. But these asserts don't work because hydra
    #   gives us the list of params as a string.
    # assert ("bcs" not in sweep_params) or (len(sweep_params["bcs"]) == 1)
    # assert ("x_bins" not in sweep_params) and ("y_bins" not in sweep_params)
    # Create an archive to contain the best individuals over all sweeps
    sweep_archive_path = os.path.join(eval_dir, "sweep_archive.pkl") 

    if cfg.reuse_sweep_archive:
        with open(sweep_archive_path, "rb") as f:
            sweep_archive = pickle.load(f)
    else:
        sweep_archive = np.full((cfg.x_bins, cfg.y_bins), None, dtype=object)
        for exp_cfg in sweep_configs:
            exp_dir = get_exp_dir(exp_cfg)
            if cfg.eval_swiss_cheese:
                archive_file = os.path.join(
                    exp_dir, "swiss_cheese_archive.pkl"
                )
                with open(archive_file, "rb") as f:
                    exp_archive = pickle.load(f)
            elif cfg.eval_cheesestring:
                archive_file = os.path.join(
                    exp_dir, "cheesestring_archive.pkl"
                )
                with open(archive_file, "rb") as f:
                    exp_archive = pickle.load(f)
            else:
                archive_files = get_archive_files(exp_dir)
                if len(archive_files) == 0:
                    print(f"Skipping {exp_dir} because it has no archives.")
                    continue
                exp_archive = load_latest_archive(exp_dir, archive_files)

            # Update the sweep archive with the best individuals from the current
            #   experiment.
            for x in range(cfg.x_bins):
                for y in range(cfg.y_bins):
                    incumbent = sweep_archive[x, y]
                    best_ind = exp_archive[x, y]
                    if best_ind is None:
                        continue
                    if best_ind.score > 1.0:
                        for c, k in best_ind.engine.fortress.CHAR_VISIT_TREE.items():
                            if len(k['nodes']) > len(best_ind.engine.fortress.CHARACTER_DICT[c].nodes):
                                breakpoint()
                            if len(k['edges']) > len(best_ind.engine.fortress.CHARACTER_DICT[c].edges):
                                breakpoint()
                        breakpoint()

                    if incumbent is None or best_ind.score > incumbent.score:
                        sweep_archive[x, y] = best_ind

        # Save the sweep archive and a heatmap
        with open(sweep_archive_path, "wb") as f:
            pickle.dump(sweep_archive, f)

    # Evaluate 
    if cfg.eval_sweep_archive:
        reeval_sweep_archive = np.array(
            [[None for _ in range(cfg.y_bins)] for _ in range(cfg.x_bins)],
            dtype=object
        )
        print("You're evaluated individuals in all experiments already. You "
              "sure you want to re-evaluate the sweep archive too? This is "
              "currently only here for some speedy last-minute eval :)")
        valid_xys = np.argwhere(sweep_archive != None)
        np.random.shuffle(valid_xys)
        for xy in valid_xys:
            ind: EvoIndividual = sweep_archive[tuple(xy)]
            print(f"Re-evaluating ind at {xy}")
            print(f"bc vals: {ind.bc_sim_vals}")
            if ind is None:
                continue
            if not hasattr(ind, 'instance_entropy'):
                ind.instance_entropy = 0
            
            # TODO: remove this backward compatibility hack for runs after 30 onward
            ind.bc_funcs = [bc_funcs[k] for k in cfg.bcs]

            ind.simulate_fortress(
                map_elites=True, n_new_sims=1, 
                n_steps_per_episode=cfg.n_steps_per_episode,
                eval_instance_entropy=True,
            )
            print(f"new bc vals: {ind.bc_sim_vals}")
            print(f"new instance entropy: {ind.instance_entropy}")
            if ind is None:
                continue

            reeval_sweep_archive[xy] = ind

        # Save the reevaluated sweep archive and a heatmap
        reeval_sweep_archive_path = os.path.join(eval_dir, "reeval_sweep_archive.pkl")
        with open(reeval_sweep_archive_path, "wb") as f:
            pickle.dump(reeval_sweep_archive, f)

        reeval_sweep_fits = np.vectorize(
            lambda x: x.score if x is not None else np.nan)(reeval_sweep_archive)
        plot_archive_heatmap(sweep_configs[0], reeval_sweep_fits, bc_bounds,
                                os.path.join(eval_dir, "reeval_best_fits.png"))

        reeval_sweep_instance_entropies = np.vectorize(
            lambda x: x.instance_entropy if x is not None else np.nan)(reeval_sweep_archive)

        

    sweep_fits = np.vectorize(
        lambda x: x.score if x is not None else np.nan)(sweep_archive)

    # Record the best fitness, QD score, and archive size to json
    best_fit = np.nanmax(sweep_fits)
    best_fit_xy = \
        np.unravel_index(np.nanargmax(sweep_fits), sweep_fits.shape)
    # Convert to regular int so we can save to json
    best_fit_xy = tuple(map(int, best_fit_xy))
    best_fit_bcs = sweep_archive[best_fit_xy].bc_sim_vals
    stats = {
        "best_fit": best_fit,
        "best_fit_xy": best_fit_xy,
        "best_fit_bcs": best_fit_bcs,
        "qd_score": np.nansum(sweep_fits),
        "archive_size": np.count_nonzero(~np.isnan(sweep_fits)),
    }
    stats_json_path = os.path.join(eval_dir, "stats.json")
    with open(stats_json_path, "w") as f:
        json.dump(stats, f, indent=4)

    bc_bounds = sweep_archive[
        tuple(np.argwhere(sweep_archive != None)[0])].get_bc_bounds()
    
    plot_archive_heatmap(sweep_configs[0], sweep_fits, bc_bounds,
                         os.path.join(eval_dir, "best_fits.png"))

    # this is a dummy individual
    dummy_ind = EvoIndividual(
        config_file=sweep_configs[0].config_file,
        fitness_type=sweep_configs[0].fitness_type, render=False,
        bcs=sweep_configs[0].bcs,
        init_strat='n_nodes', # doesn't matter
        entropy_dict=None, # doesn't matter
        init_seed=0,
    )
    best_ind = sweep_archive[best_fit_xy]
    # Plot alternate heatmaps showing the values of behavior characteristics not
    #   used as axes of this archive.
    possible_bcs = list(bc_funcs.keys())
    for bc_name in possible_bcs:
        # if bc_name in cfg.bcs:
        #     continue
        sweep_vals = np.vectorize(
            lambda x: float(bc_funcs[bc_name](x)) if x is not None else np.nan)(sweep_archive)
        plot_archive_heatmap(
            sweep_configs[0], sweep_vals, bc_bounds,
            os.path.join(eval_dir, f"{bc_name}.png"), cbar_label=bc_name)

    breakpoint()
    sweep_instance_entropies = np.vectorize(
        lambda x: x.instance_entropy if x is not None else np.nan)(sweep_archive)
    plot_archive_heatmap(
        sweep_configs[0], sweep_instance_entropies, bc_bounds,
        os.path.join(eval_dir, "instance_entropies.png"),
        cbar_label="instance entropy")


@hydra.main(version_base="1.3", config_path="conf", config_name="cross_eval")
def dummy_ill_cross_eval(cfg: EvoConfig):
    # Our drill_cross_eval plugin intercepts this function call to call 
    # `ill_cross_eval`
    pass


if __name__ == '__main__':
    dummy_ill_cross_eval()
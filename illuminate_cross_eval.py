import json
import os
import pickle

import hydra
import numpy as np

from config import EvoConfig
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
                    ind = exp_archive[x, y]
                    if ind is None:
                        continue
                    if ind.score > 1.0:
                        for c, k in ind.engine.fortress.CHAR_VISIT_TREE.items():
                            if len(k['nodes']) > len(ind.engine.fortress.CHARACTER_DICT[c].nodes):
                                breakpoint()
                            if len(k['edges']) > len(ind.engine.fortress.CHARACTER_DICT[c].edges):
                                breakpoint()
                        breakpoint()

                    if incumbent is None or ind.score > incumbent.score:
                        sweep_archive[x, y] = ind

        # Save the sweep archive and a heatmap
        with open(sweep_archive_path, "wb") as f:
            pickle.dump(sweep_archive, f)

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
        json.dump(stats, f)

    bc_bounds = sweep_archive[
        tuple(np.argwhere(sweep_archive != None)[0])].get_bc_bounds()
    
    plot_archive_heatmap(sweep_configs[0], sweep_fits, bc_bounds,
                         os.path.join(eval_dir, "best_fits.png"))

    ind = sweep_archive[best_fit_xy]
    # Plot alternate heatmaps showing the values of behavior characteristics not
    #   used as axes of this archive.
    possible_bcs = list(ind.all_bc_funcs.keys())
    for bc_name in possible_bcs:
        # if bc_name in cfg.bcs:
        #     continue
        sweep_entropies = np.vectorize(
            lambda x: float(x.all_bc_funcs[bc_name]()) if x is not None else np.nan)(sweep_archive)
        plot_archive_heatmap(
            sweep_configs[0], sweep_entropies, bc_bounds,
            os.path.join(eval_dir, f"{bc_name}.png"), cbar_label=bc_name)


@hydra.main(version_base="1.3", config_path="conf", config_name="cross_eval")
def dummy_ill_cross_eval(cfg: EvoConfig):
    # Our drill_cross_eval plugin intercepts this function call to call 
    # `ill_cross_eval`
    pass


if __name__ == '__main__':
    dummy_ill_cross_eval()
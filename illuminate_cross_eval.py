import os
import pickle

import hydra
import numpy as np

from config import EvoConfig
from illuminate import get_archive_files, get_exp_dir, load_latest_archive, plot_archive_heatmap


def ill_cross_eval(cfg: EvoConfig, sweep_configs, sweep_params):
    # Create a directory for the results of the cross-evaluation.
    eval_dir = f"cross_evals/{cfg.sweep_name}"
    os.makedirs(eval_dir, exist_ok=True)
    # NOTE: Assuming bcs are the same for all configs, and that archives have 
    #   the same dimensions. But these asserts don't work because hydra
    #   gives us the list of params as a string.
    # assert ("bcs" not in sweep_params) or (len(sweep_params["bcs"]) == 1)
    # assert ("x_bins" not in sweep_params) and ("y_bins" not in sweep_params)
    # Create an archive to contain the best individuals over all sweeps
    sweep_archive = np.full((cfg.x_bins, cfg.y_bins), None, dtype=object)

    for exp_cfg in sweep_configs:
        exp_dir = get_exp_dir(exp_cfg)
        archive_files = get_archive_files(exp_dir)
        exp_archive = load_latest_archive(exp_dir, archive_files)

        # Update the sweep archive with the best individuals from the current
        #   experiment.
        for x in range(cfg.x_bins):
            for y in range(cfg.y_bins):
                incumbent = sweep_archive[x, y]
                ind = exp_archive[x, y]
                if ind is None:
                    continue
                if incumbent is None or ind.score > incumbent.score:
                    sweep_archive[x, y] = ind
    sweep_fits = np.vectorize(
        lambda x: x.score if x is not None else np.nan)(sweep_archive)

    bc_bounds = sweep_archive[
        tuple(np.argwhere(sweep_archive != None)[0])].get_bc_bounds()
    
    # Save the sweep archive and a heatmap
    with open(os.path.join(eval_dir, "sweep_archive.pkl"), "wb") as f:
        pickle.dump(sweep_archive, f)

    plot_archive_heatmap(cfg, sweep_fits, bc_bounds,
                         os.path.join(eval_dir, "best_fits.png"))


@hydra.main(version_base="1.3", config_path="conf", config_name="cross_eval")
def dummy_ill_cross_eval(cfg: EvoConfig):
    # Our drill_cross_eval plugin intercepts this function call to call 
    # `ill_cross_eval`
    pass


if __name__ == '__main__':
    dummy_ill_cross_eval()
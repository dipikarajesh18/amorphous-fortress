import os
import pickle
import random
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from config import EvoConfig


# create a new id for the entity (copied from `entities.py` but abstracted a bit so we can use it for the reference)
def newID(all_ids,id_len=4):
    all_num = list(range(16**4))
    while len(all_num) > 0:
        i = f'%{id_len}x' % random.choice(all_num)
        if i not in all_ids:
            return i
        all_num.remove(int(i,16))

    return f'%0{id_len}x' % random.randrange(16**(id_len+1))


def get_bin_idx(val, bounds, n_bins):
    return int((val - bounds[0]) / (bounds[1] - bounds[0]) * (n_bins - 1))


def get_xy_from_bcs(bc: tuple, bc_bounds: tuple, x_bins: int, y_bins: int):
    x = get_bin_idx(bc[0], bc_bounds[0], x_bins)
    y = get_bin_idx(bc[1], bc_bounds[1], y_bins)
    return (x, y)


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
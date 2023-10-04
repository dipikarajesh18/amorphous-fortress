import numpy as np
from scipy.stats import entropy

from utils import get_bin_idx


def gen_entropy_dict(n_fsm_size_bins, n_fsms, n_entropy_bins):
    """Generate a dictionary mapping bins of entropy values over bins of 
    fsm sizes."""
    combinations = np.array(list(sum_combinations(n_fsm_size_bins, n_fsms)))
    combinations_normed = combinations / combinations.sum(axis=1)[:, None]
    entropies = entropy(combinations_normed, axis=1, base=n_fsm_size_bins)
    entropy_bins = [get_bin_idx(e, (0.0, 1.0), n_entropy_bins) for e in entropies]

    ent_idxs_to_combinations = {}
    for i, e in enumerate(entropy_bins):
        if e not in ent_idxs_to_combinations:
            ent_idxs_to_combinations[e] = []
        ent_idxs_to_combinations[e].append(combinations[i])

    return ent_idxs_to_combinations


def sum_combinations(N, M, current_sum=0, current_list=[]):
    # Base cases
    if len(current_list) == N:
        if current_sum == M:
            yield current_list
        return

    if current_sum > M:
        return

    # Start next number either from 0 or the last number in the list to avoid duplicate combinations
    start = current_list[-1] if current_list else 0
    for i in range(start, M + 1):
        new_list = current_list + [i]
        yield from sum_combinations(N, M, current_sum + i, new_list)

if __name__ == '__main__':
    # Example usage:
    N, M = 15, 15
    combinations = list(sum_combinations(N, M))
    print(f"Combinations of {N} numbers that sum to {M}:")
    for c in combinations:
        print(c)

    print(f"Total combinations: {len(list(combinations))}")

    # Convert the list of lists to a 2D numpy array.
    combinations = np.array(combinations)
    # Normalize each row to sum to 1.
    combinations = combinations / combinations.sum(axis=1)[:, None]
    # Get the entropy of each row.
    entropies = entropy(combinations.T, base=N)

    print(f"Entropy of each combination:")
    for e in entropies:
        print(e)

    # Plot the entropy distribution.
    import matplotlib.pyplot as plt
    plt.hist(entropies, bins=100)
    plt.savefig('entropy.png')
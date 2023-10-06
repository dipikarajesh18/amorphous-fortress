import dataclasses
from hydra.core.config_store import ConfigStore
from dataclasses import dataclass


@dataclass
class EvoConfig:
    # Path to config file
    config_file: str = "CONFIGS/beta_config.yaml"
    # Render the simulation
    render: bool = False
    # Number of generations to evolve for
    generations: int = 10000
    # Probability of mutating an edge
    edge_coin: float = 0.5
    # Probability of mutating a node
    node_coin: float = 0.5
    # Probability of adding or removing an entity instance
    instance_coin: float = 0.5
    # Running the alife experiment
    alife_exp: bool = False
    # Population size
    pop_size: int = 10
    # Number of bins for x axis
    x_bins: int = 100
    # Number of bins for y axis
    y_bins: int = 100
    # Number of generations between checkpoints
    checkpoint_frequency: int = 10
    # Number of generations between plots
    plot_frequency: int = 10
    # Random seed for the experiment
    seed: int = 0
    # Iterate through individuals in the archive and render them in the terminal using curses
    enjoy: bool = False
    # Re-evaluate the archive on new seeds
    eval_swiss_cheese: bool = False
    # Re-evaluate with longer episodes to see if more fortresses overpopulate/extinguish than before
    eval_cheesestring: bool = False
    # Overwrite existing experiment directory
    overwrite: bool = False
    # Percent of random individuals to add to the population
    percent_random: float = 0.1
    # Fitness type: 'tree' or 'M'
    fitness_type: str = "tree"
    # Behavior characteristics to use for evaluation
    # bcs: list = ['n_entities', 'n_nodes']
    # User defaults factory
    bcs: list = dataclasses.field(default_factory=lambda: ['n_entities', 'n_nodes'])
    # Number of processes to use for simulation
    n_proc: int = 10
    # Number of simulations to run per evaluation
    n_sims: int = 5
    # Number of steps per episode
    n_steps_per_episode: int = 100
    # Name of hyperparameter sweep (if applicable)
    sweep_name: str = "none"
    # When aggregating archives for cross-evaluation, re-aggregate rather than
    #  reusing the existing sweep archive.
    reuse_sweep_archive: bool = False


cs = ConfigStore.instance()
cs.store(name="evolve_base", node=EvoConfig)


# parser.add_argument("-c", "--config", type=str, default="CONFIGS/beta_config.yaml", help='Path to config file')
# parser.add_argument("-r", "--render", action="store_true", help="Render the simulation")
# parser.add_argument("-g", "--generations", type=int, default=1000, help='Number of generations to evolve for')
# parser.add_argument("-e", "--edge_coin", type=float, default=0.5, help='Probability of mutating an edge')
# parser.add_argument("-n", "--node_coin", type=float, default=0.5, help='Probability of mutating an node')
# parser.add_argument("-i", "--instance_coin", type=float, default=0.5, help='Probability of adding or removing an entity instance')
# parser.add_argument("-a", "--alife_exp", action="store_true", help="Running the alife experiment")
# parser.add_argument("-p", "--pop_size", type=int, default=10, help="Population size")
# parser.add_argument("-xb", "--x_bins", type=int, default=100, help="Number of bins for x axis")
# parser.add_argument("-yb", "--y_bins", type=int, default=100, help="Number of bins for y axis")
# parser.add_argument("-cf", "--checkpoint_frequency", type=int, default=10, help="Number of generations between checkpoints")
# parser.add_argument("-pf", "--plot_frequency", type=int, default=10, help="Number of generations between plots")
# parser.add_argument("-s", "--seed", type=int, default=0, help="Random seed for the experiment")
# parser.add_argument("-ev", "--evaluate", action="store_true", help="Evaluate the archive")
# parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing experiment directory")
# parser.add_argument("-pr", "--percent_random", type=float, default=0.1, help="Percent of random individuals to add to the population")
# parser.add_argument("-ft", "--fitness_type", type=str, default="tree", help="Fitness type: 'tree' or 'M'")
# parser.add_argument("-bcs", "--bcs", type=str, nargs="+", default=['n_entities', 'n_nodes'], help="Behavior characteristics to use for evaluation")
# parser.add_argument("-np", "--n_proc", type=int, default=1, help="Number of processes to use for simulation")
# parser.add_argument("-ns", "--n_sims", type=int, default=5, help="Number of simulations to run per evaluation")
# parser.add_argument("-nse", "--n_steps_per_episode", type=int, default=100, help="Number of steps per episode")
import copy
import curses
import pickle
import random
import time
from typing import List

import numpy as np
from scipy.stats import entropy

from engine import Engine
from entities import NODE_DICT, Entity
from render_curses import curses_render_loop, init_screens
from utils import get_bin_idx


def get_n_nodes_and_edges(self):
    return self.fsm_stats['n_nodes'] + self.fsm_stats['n_edges']

def get_n_edges(self):
    return self.fsm_stats['n_edges']

def get_n_nodes(self):
    return self.fsm_stats['n_nodes']

def get_n_entities(self):
    return min(len(self.engine.fortress.entities), self.engine.fortress.max_entities)

def get_entropy(self):
    if not self.entropy_is_stale:
        return self.ent_val
    # Get entropy of number of nodes per entity, binning into as many bins as there are entity types
    bin_idxs = [
        get_bin_idx(e-1, (1, self.max_nodes_per_entity), 
                    n_bins=self.n_entity_types
        ) 
                    for e in self.n_nodes_per_ent]
    unique, counts = np.unique(bin_idxs, return_counts=True)
    # Pad counts so with 0s so that the number of bins is equal to the number of entity types
    counts = np.pad(counts, (0, self.n_entity_types - len(counts)), mode='constant')
    bin_probs = counts / np.sum(counts)
    # print(f"bin_probs: {bin_probs}")
    self.ent_val = entropy(bin_probs, base=len(bin_probs))
    # if np.isnan(self.ent_val):
    #     breakpoint()
    self.ent_val = 0 if np.isnan(self.ent_val) else self.ent_val
    # print(f"Entropy: {self.ent_val}")
    self.entropy_is_stale = False
    # print(bin_probs)

    # Make sure our entropy calculation here matches up with the one intended
    #   when the individual was initialized (only valid pre-mutation!)
    fsm_size_bin_dist = np.unique(bin_idxs, return_counts=True)

    return self.ent_val

bc_funcs = {
    'n_entities': get_n_entities,
    'n_nodes': get_n_nodes,
    'n_nodes_and_edges': get_n_nodes_and_edges,
    'n_edges': get_n_edges,
    'entropy': get_entropy,
}


class EvoIndividual():
    engine: Engine

    def __init__(self, config_file: str, fitness_type: str, bcs: List[str],
                 render: bool = False, init_strat='n_nodes', entropy_dict=None,
                 init_seed=None):
        self.config_file = config_file
        self.score = 0
        self.bc_sim_vals = (0, 0)
        self.instance_entropy = 0
        self.n_sims = 0
        init_seed = random.randint(0, 1000000) if init_seed is None else init_seed
        engine = Engine(config_file, init_seed=init_seed)
        self.engine = engine
        self.render = render

        # self.n_sim_steps = 100
        self.fitness_type = fitness_type

        self.init_fortress_str = ""

        self.all_bc_funcs = bc_funcs
        if init_strat == 'entropy':
            assert entropy_dict is not None
        self.engine.populateFortress(
            init_strat=init_strat, entropy_dict=entropy_dict)
        self.get_fsm_stats()
        self.n_entity_types = len(self.engine.fortress.CHARACTER_DICT)
        max_aggregate_fsm_nodes = self.engine.fortress.max_aggregate_fsm_nodes
        self.max_nodes_per_entity = max_aggregate_fsm_nodes / self.n_entity_types
        max_aggregate_edges = (self.max_nodes_per_entity ** 2) * self.n_entity_types
        bc_bounds = {
            'n_entities': (0, self.engine.fortress.max_entities),
            # each node at least has one idle node with a self-edge
            'n_nodes': (self.n_entity_types, max_aggregate_fsm_nodes),
            'n_edges': (1, max_aggregate_edges),
            'n_nodes_and_edges': (0, max_aggregate_fsm_nodes + max_aggregate_edges),
            'entropy': (0, 1),
        } 

        self.bc_bounds = []
        for bc in bcs:
            self.bc_bounds.append(bc_bounds[bc])

        self.bc_funcs = []
        for bc in bcs:
            self.bc_funcs.append(bc_funcs[bc])

        self.entropy_is_stale = True

    def get_n_nodes_and_edges(self):
        return self.fsm_stats['n_nodes'] + self.fsm_stats['n_edges']

    def get_n_edges(self):
        return self.fsm_stats['n_edges']

    def get_n_nodes(self):
        return self.fsm_stats['n_nodes']

    def get_instance_entropy(self):
        # First count how many instances of each entity type there are
        unique, counts = np.unique(
            [e.char for e in self.engine.fortress.entities.values()],
            return_counts=True
        )
        counts = np.pad(counts, (0, self.n_entity_types - len(counts)), 
                        mode='constant', constant_values=0)
        bin_idxs = [
            get_bin_idx(e, (0, self.engine.fortress.max_entities),
                        n_bins=self.n_entity_types
            )
            for e in counts
        ]
        unique, bin_counts = np.unique(bin_idxs, return_counts=True)
        bin_counts = np.pad(
            bin_counts, (0, self.n_entity_types - len(bin_counts)),
            mode='constant', constant_values=0)
        bin_probs = bin_counts / np.sum(bin_counts)
        instance_ent_val = entropy(bin_probs, base=len(bin_probs))
        return instance_ent_val

    def get_entropy(self):
        if not self.entropy_is_stale:
            return self.ent_val
        # Get entropy of number of nodes per entity, binning into as many bins as there are entity types
        bin_idxs = [
            get_bin_idx(e-1, (1, self.max_nodes_per_entity), 
                        n_bins=self.n_entity_types
            ) 
                        for e in self.n_nodes_per_ent]
        unique, counts = np.unique(bin_idxs, return_counts=True)
        # Pad counts so with 0s so that the number of bins is equal to the number of entity types
        counts = np.pad(counts, (0, self.n_entity_types - len(counts)),
                        mode='constant', constant_values=0)
        bin_probs = counts / np.sum(counts)
        # print(f"bin_probs: {bin_probs}")
        self.ent_val = entropy(bin_probs, base=len(bin_probs))
        # if np.isnan(self.ent_val):
        #     breakpoint()
        self.ent_val = 0 if np.isnan(self.ent_val) else self.ent_val
        # print(f"Entropy: {self.ent_val}")
        self.entropy_is_stale = False
        # print(bin_probs)

        # Make sure our entropy calculation here matches up with the one intended
        #   when the individual was initialized (only valid pre-mutation!)
        # fsm_size_bin_dist = np.unique(bin_idxs, return_counts=True)

        return self.ent_val

    def mutate_ind(self, args):
        """Mutate the fortress by mutating entity class FSMs or the placement of entity instances on the initial map."""
        # do not inherit fitness/BCs from parents
        self.n_sims = 0
        self.score = 0
        self.bc_sim_vals = (0, 0)
        self.instance_entropy = 0

        # mutate randomly
        edge_rando = random.random()
        node_rando = random.random()
        instance_rando = random.random()

        while edge_rando < args.edge_coin:
            self.mutateFSMEdges()
            edge_rando = random.random()
        
        if node_rando < args.node_coin:
            self.mutateFSMNodes()

        while instance_rando < args.instance_coin:
            self.mutateEnt()
            instance_rando = random.random()

        self.entropy_is_stale = True
        self.get_fsm_stats()

    def clone(self):
        """Clone the individual."""

        # # FIXME: Why does this not work? Lots of empty maps...?
        # clone = EvoIndividual(self.config_file, self.render)
        # clone.engine.ref_ents = copy.deepcopy(self.engine.ref_ents)
        # # This is weird. We generate a new base set of entities from which to clone when adding new ones. A very roundabout way of doing things.
        # # TODO: When adding new random entities in mutation, create the entity from scratch right there.
        # clone.engine.fortress.makeCharacters()
        # return clone

        # The sketchy way...
        return copy.deepcopy(self)

    # # f init_random_fortress(self):
    #     self.engine.populateFortress()
    #     self.n_entity_types = len(self.engine.fortress.CHARACTER_DICT)

    def mutateEnt(self):
        """Add or delete an entity from the initial map."""
        i = random.randint(0, 1)
        if i == 0 and len(self.engine.init_ents) > 0:
            # Remove a random entity
            ent_id = random.choice(range(len(self.engine.init_ents)))
            del self.engine.init_ents[ent_id]
            # print(f'Removed entity {ent_id}, char {ent.char}, at {ent.pos}')
        elif i == 1:
            # Add a random entity
            # c = random.choice(list(self.engine.fortress.CHARACTER_DICT.keys()))
            x, y = random.randint(1, self.engine.fortress.width - 2), random.randint(1, self.engine.fortress.height - 2)
            # ent: Entity = self.engine.fortress.CHARACTER_DICT[c].clone((x, y))

            c = random.choice(self.engine.fortress.CONFIG['character'])
            self.engine.init_ents.append({'char':c, 'pos':[x, y]})


    # only change the nodes of an entity type
    def mutateFSMNodes(self):
        i = random.randint(0, 2)
        ent_id = random.choice(list(self.engine.fortress.CHARACTER_DICT.keys()))
        ent: Entity = self.engine.fortress.CHARACTER_DICT[ent_id]

        # TODO: We don't need this. Just use `ent.avail_node_types`. Useful for debugging the latter though.
        # find the nodes already available
        # avail_nodes = []
        # for node in self.engine.fortress.CONFIG['action_space'].copy():
        # for node in self.engine.fortress.node_types:
        #     if node not in ent.nodes:
        #         avail_nodes.append(node)
        # assert len(avail_nodes) == len(ent.avail_node_types)
        # if len(avail_nodes) != len(ent.avail_node_types):
        #     breakpoint()

        # delete a random node 
        if i == 0 and len(ent.nodes) > 1:
            idxs = np.arange(len(ent.nodes) - 1) + 1
            vals = 1 / idxs
            vals = vals / np.sum(vals)
            n_to_delete = np.random.choice(idxs, p=vals)
            # print(f"Removing {n_to_delete} nodes from entity {ent_id}")
            for _ in range(n_to_delete):
                node_ind = random.choice(range(len(ent.nodes)))
                node_str = ent.nodes[node_ind]
                del ent.nodes[node_ind]
                ent.killOrphanEdges(node_ind)
                # print(f"Removed node {node_str} from entity {ent_id}")
                ent.avail_node_types.append(node_str)
                # ent.avail_node_types.add(node_str)
                # print(f'Removed node {node_id} from entity {ent_id}')

        # add a node
        elif i == 1 and len(ent.avail_node_types) > 0:
            idxs = np.arange(len(ent.avail_node_types)) + 1
            vals = 1 / idxs
            vals = vals / np.sum(vals)
            n_to_add = np.random.choice(idxs, p=vals)
            assert n_to_add <= len(ent.avail_node_types)
            # print(f"Adding {n_to_add} nodes to entity {ent_id}")
            for _ in range(n_to_add):
                # rand_anode = random.choice(tuple(ent.avail_node_types))
                rand_anode = random.choice(ent.avail_node_types)
                
                new_node = f"{rand_anode} "
    
                ent.nodes.append(new_node.strip())
                ent.connectAnnieNode(len(ent.nodes)-1)
                ent.avail_node_types.remove(rand_anode)
                # print(f'Added node {node} to entity {ent_id}')

        # change a node to another available node
        elif i == 2:
            idxs = np.arange(len(ent.nodes)) + 1
            vals = 1 / idxs
            vals = vals / np.sum(vals)
            n_to_change = np.random.choice(idxs, p=vals)
            # print(f"Changing {n_to_change} nodes in entity {ent_id}")

            for _ in range(n_to_change):
                if len(ent.avail_node_types) > 0:
                    node_ind = random.choice(range(len(ent.nodes)))
                    # rand_anode = random.choice(tuple(ent.avail_node_types))
                    rand_anode = random.choice(ent.avail_node_types)
                    new_node = f"{rand_anode}"
                    old_node = ent.nodes[node_ind]

                    ent.nodes[node_ind] = new_node.strip()
                    # ent.avail_node_types.add(old_node)
                    ent.avail_node_types.append(old_node)
                    ent.avail_node_types.remove(new_node)
                    # print(f'Changed node {node_id} to {rand_anode} in entity {ent_id}')
                    
                # swap 2 nodes
                else:
                    node_ind1 = random.choice(range(len(ent.nodes)))
                    node_ind2 = random.choice(range(len(ent.nodes)))
                    ent.nodes[node_ind1], ent.nodes[node_ind2] = ent.nodes[node_ind2], ent.nodes[node_ind1]
                    # print(f'Swapped nodes {node_ind1} and {node_ind2} in entity {ent_id}')
                
        # #3 does nothing :D
        # ent.validate_avail_nodes()
        # print('YA VALID\n')


    # only change the edges of an entity
    def mutateFSMEdges(self):
        i = random.randint(0, 2)
        ent_id = random.choice(list(self.engine.fortress.CHARACTER_DICT.keys()))
        ent = self.engine.fortress.CHARACTER_DICT[ent_id]

        # delete an edge
        if i == 0 and len(ent.edges) > 1:
            edge_ind = random.choice(list(ent.edges.keys()))
            del ent.edges[edge_ind]
            ent.connectOrphanNodes()
            # print(f'Removed edge {edge_ind} from entity {ent_id}')
        
        # add an edge
        elif i == 1:
            node_ind1 = random.choice(range(len(ent.nodes)))
            node_ind2 = random.choice(range(len(ent.nodes)))
            ent.edges[f"{node_ind1}-{node_ind2}"] = ent.newEdge()
            # print(f'Added edge from node {node_ind1} to node {node_ind2} in entity {ent_id}')

        # change an edge
        elif i == 2:
            if len(ent.edges) > 0:
                edge_ind = random.choice(list(ent.edges.keys()))
                ent.edges[edge_ind] = ent.newEdge()

    def update(self, ret, map_elites, eval_instance_entropy=False):
        """ multiprocessing hack"""
        ret, self.n_sims = ret
        if not map_elites:
            if eval_instance_entropy:
                self.score, self.instance_entropy = ret
            else:
                self.score = ret
        else:
            if eval_instance_entropy:
                self.score, self.bc_sim_vals, self.instance_entropy = ret
            else:
                self.score, self.bc_sim_vals = ret

    def simulate_fortress(
            self, show_prints=False, map_elites=False, n_new_sims=5,
            n_steps_per_episode=100, verbose=False, eval_instance_entropy=False
        ):

        metrics = []
        for i in range(n_new_sims):
            self.engine.fortress.rng_sim = np.random.default_rng(i + self.n_sims)
            m = self.simulate_fortress_once(
                show_prints, map_elites, n_steps=n_steps_per_episode,
                eval_instance_entropy=eval_instance_entropy,
            )
            metrics.append(m)
        
        self.n_sims += len(metrics)
        if not map_elites:
            self.score = (
                (self.score * (self.n_sims - n_new_sims) 
                + sum([m[0] for m in metrics])) 
                / self.n_sims
            )
            ret = self.score
        if map_elites:
            # TODO: vectorize this
            self.score = (
                (self.score * (self.n_sims - n_new_sims)
                + sum([m[0] for m in metrics]))
                / self.n_sims
            )
            bc_0 = (
                (self.bc_sim_vals[0] * (self.n_sims - n_new_sims)
                + sum([m[1] for m in metrics]))
                / self.n_sims
            )
            bc_1 = (
                (self.bc_sim_vals[1] * (self.n_sims - n_new_sims)
                + sum([m[2] for m in metrics]))
                / self.n_sims
            )
            self.bc_sim_vals = (bc_0, bc_1)
            ret = self.score, self.bc_sim_vals
        if eval_instance_entropy:
            self.instance_entropy = (
                (self.instance_entropy * (self.n_sims - n_new_sims)
                + sum([m[-1] for m in metrics]))
                / self.n_sims
            ) 
        if verbose:
            print(f"Score: {self.score}")
        return ret, self.n_sims
            
    def simulate_fortress_once(
            self, show_prints=False, map_elites=False, n_steps=100,
            eval_instance_entropy=False,):
        """Reset and simulate the fortress."""
        self.engine.resetFortress()

        self.init_fortress_str = self.engine.fortress.renderEntities()

        if self.render:
            screen_set, screen_dims = init_screens()

        loops = 0
        while not (self.engine.fortress.terminate() or self.engine.fortress.inactive() or \
                   self.engine.fortress.overpop() or loops >= n_steps):
            # print(self.engine.fortress.renderEntities())
            self.engine.update(True)
            if self.render:
                curses_render_loop(screen_set, screen_dims, self.engine)
                time.sleep(0.1)
            # print(loops)
            loops+=1

        if self.render:
            curses.endwin()

        # print(self.engine.fortress.renderEntities())
        if not eval_instance_entropy:
            instance_entropy = 0
        else:
            instance_entropy = self.get_instance_entropy()

        if not map_elites:
            if self.fitness_type == "M":
                score = compute_fortress_score_dummy(self.engine)
            elif self.fitness_type == "tree":
                self.get_fsm_stats()
                score = self.fsm_stats['prop_visited']
            return score, instance_entropy
        elif map_elites:
            if self.fitness_type == "M":
                score = compute_fortress_score_dummy(self.engine)
                bc_0 = self.get_n_entities()
                bc_1 = len([e for e in self.engine.fortress.entities.values() if e.char == '@'])
            elif self.fitness_type == "tree":
                self.get_fsm_stats(show_prints)
                score = self.fsm_stats['prop_visited']
                bc_0, bc_1 = self.bc_funcs[0](self), self.bc_funcs[1](self)
            return score, bc_0, bc_1, instance_entropy

    def get_n_entities(self):
        return min(len(self.engine.fortress.entities), self.engine.fortress.max_entities)

    # export the evo individual to a file as pickle to reload object
    def expEvoInd(self, filename):
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    # import the evo individual from a file as pickle to reload object
    def impEvoInd(self, filename):
        with open(filename, 'rb') as input:
            self = pickle.load(input)

    def get_bc_bounds(self):
        if self.fitness_type == "M":
            bc_0_bounds = (0, self.engine.fortress.max_entities) 
            bc_1_bounds = (0, self.engine.fortress.max_entities)
        elif self.fitness_type == "tree":
            return self.bc_bounds
        return (bc_0_bounds, bc_1_bounds)

    def get_fsm_stats(self, print_debug=False):
        """Compute the score of a fortress. for realsies"""
        engine = self.engine
        n_visited_nodes = 0
        n_visited_edges = 0
        n_total_nodes = 0
        n_total_edges = 0
        self.n_nodes_per_ent = []
        for c, k in engine.fortress.CHAR_VISIT_TREE.items():
            n_visited_nodes += len(k['nodes'])
            n_nodes_c = len(engine.fortress.CHARACTER_DICT[c].nodes)
            self.n_nodes_per_ent.append(n_nodes_c)
            n_visited_edges += len(k['edges'])
            n_total_edges += len(engine.fortress.CHARACTER_DICT[c].edges)
        n_total_nodes = sum(self.n_nodes_per_ent)

        n_unvisited_nodes = n_total_nodes - n_visited_nodes
        n_unvisited_edges = n_total_edges - n_visited_edges

        visit = n_visited_nodes + n_visited_edges
        unvisit = n_unvisited_nodes + n_unvisited_edges
        tree_size = n_total_edges + n_total_nodes

        # if print_debug: 
        #     print("::::::::::::")
        #     print(f"Total # nodes + edges: {n_total_edges + n_total_nodes}")
        #     print(f"Visited (n/e): {n_visited_nodes} / {n_visited_edges}")
        #     print(f"Unvisited (n/e): {n_unvisited_nodes} / {n_unvisited_edges}")
        #     print("::::::::::::")

        prop_visited = (visit / tree_size)
        self.fsm_stats = {
            'prop_visited': prop_visited,
            'n_nodes': n_total_nodes,
            'n_edges': n_total_edges,
            'n_nodes_per_ent': self.n_nodes_per_ent,
        }


# counts the number of M's in the fortress
def compute_fortress_score_dummy(engine: Engine):
    """Compute the score of a fortress."""
    score = 0
    for ent in engine.fortress.entities.values():
        score += ent.char == 'M'
    return score


    # n_unvisited = (n_total_nodes - n_visited_nodes) + (n_total_edges - n_visited_edges)
    # return n_visited_nodes + n_visited_edges - n_unvisited*1


def mutate_and_eval_ind(ind: EvoIndividual, generation: int, args):
    ind.mutate_ind(ind, args)
    show_prints = generation % 25 == 0
    ind.simulate_fortress(show_prints=show_prints)
    return ind


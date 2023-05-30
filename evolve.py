"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import copy
import curses
import random
import math
import pickle
import cProfile
import matplotlib.pyplot as plt

import argparse
import numpy as np

from engine import Engine
from entities import Entity
# from main import curses_render_loop, init_screens, DEBUG
from utils import newID

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.



class EvoIndividual():

    def __init__(self, config_file: str, render: bool = False):
        self.config_file = config_file
        self.score = None
        engine = Engine(config_file)
        self.engine = engine
        self.render = render

        self.n_sim_steps = 20
        self.fitness_type = "tree"

        self.init_fortress_str = ""

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

    def init_random_fortress(self):
        self.engine.populateFortress()

    # adds or deletes an entity
    def mutateEnt(self):
        """Mutate the fortress."""
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

        self.score = None

    # only change the nodes of an entity
    def mutateFSMNodes(self):
        i = random.randint(0, 2)
        ent_id = random.choice(list(self.engine.fortress.CHARACTER_DICT.keys()))
        ent = self.engine.fortress.CHARACTER_DICT[ent_id]

        # find the nodes already available
        avail_nodes = []
        for node in self.engine.fortress.CONFIG['action_space'].copy():
            if node not in ent.nodes:
                avail_nodes.append(node)

        # delete a random node 
        if i == 0 and len(ent.nodes) > 1:
            node_ind = random.choice(range(len(ent.nodes)))
            del ent.nodes[node_ind]
            ent.killOrphanEdges(node_ind)
            # print(f'Removed node {node_id} from entity {ent_id}')


        # add a node
        elif i == 1 and len(avail_nodes) > 0:
            rand_anode = random.choice(avail_nodes)
            
            new_node = f"{rand_anode} "

            # add the arguments to the node
            if ent.NODE_DICT[rand_anode]['args'] != []:
                for arg in ent.NODE_DICT[rand_anode]['args']:
                    if arg == "entityChar":
                        new_node += f"{random.choice(self.engine.fortress.CONFIG['character'])} "
            
            ent.nodes.append(new_node.strip())
            ent.connectAnnieNode(len(ent.nodes)-1)
            # print(f'Added node {node} to entity {ent_id}')

        # change a node to another available node
        elif i == 2:
            if len(avail_nodes) > 0:
                node_ind = random.choice(range(len(ent.nodes)))
                rand_anode = random.choice(avail_nodes)
                new_node = f"{rand_anode} "

                # add the arguments to the node
                if ent.NODE_DICT[rand_anode]['args'] != []:
                    for arg in ent.NODE_DICT[rand_anode]['args']:
                        if arg == "entityChar":
                            new_node += f"{random.choice(self.engine.fortress.CONFIG['character'])} "

                ent.nodes[node_ind] = new_node.strip()
                # print(f'Changed node {node_id} to {rand_anode} in entity {ent_id}')
                

            # swap 2 nodes
            else:
                node_ind1 = random.choice(range(len(ent.nodes)))
                node_ind2 = random.choice(range(len(ent.nodes)))
                ent.nodes[node_ind1], ent.nodes[node_ind2] = ent.nodes[node_ind2], ent.nodes[node_ind1]
                # print(f'Swapped nodes {node_ind1} and {node_ind2} in entity {ent_id}')
                
        # #3 does nothing :D


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
            

    def simulate_fortress(self,generation):
        """Reset and simulate the fortress."""
        self.engine.resetFortress()

        self.init_fortress_str = self.engine.fortress.renderEntities()

        # if self.render:
        #     screen_set, screen_dims = init_screens()

        loops = 0
        while not (self.engine.fortress.terminate() or self.engine.fortress.inactive() or \
                   self.engine.fortress.overpop() or loops >= self.n_sim_steps):
            # print(self.engine.fortress.renderEntities())
            self.engine.update(True)
            # if self.render:
            #     curses_render_loop(screen_set, screen_dims, self.engine)
            # print(loops)
            loops+=1

        if self.render:
            curses.endwin()

        print(self.engine.fortress.renderEntities())

        if self.fitness_type == "M":
            self.score = compute_fortress_score_dummy(self.engine)
        elif self.fitness_type == "tree":
            show_prints = generation%25==0
            self.score = compute_fortress_score(self.engine,show_prints)

    # export the evo individual to a file as pickle to reload object
    def expEvoInd(self, filename):
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    # import the evo individual from a file as pickle to reload object
    def impEvoInd(self, filename):
        with open(filename, 'rb') as input:
            self = pickle.load(input)



# counts the number of M's in the fortress
def compute_fortress_score_dummy(engine: Engine):
    """Compute the score of a fortress."""
    score = 0
    for ent in engine.fortress.entities.values():
        score += ent.char == 'M'
    return score


# actual fitness function
# calculates how many tree traversal of a entity class - more traversal = better fitness
def compute_fortress_score(engine: Engine, print_debug=False):
    """Compute the score of a fortress. for realsies"""
    n_visited_nodes = 0
    n_visited_edges = 0
    n_total_nodes = 0
    n_total_edges = 0
    for c, k in engine.fortress.CHAR_VISIT_TREE.items():
        n_visited_nodes += len(k['nodes'])
        n_total_nodes += len(engine.fortress.CHARACTER_DICT[c].nodes)
        n_visited_edges += len(k['edges'])
        n_total_edges += len(engine.fortress.CHARACTER_DICT[c].edges)

    n_unvisited_nodes = n_total_nodes - n_visited_nodes
    n_unvisited_edges = n_total_edges - n_visited_edges

    visit = n_visited_nodes + n_visited_edges
    unvisit = n_unvisited_nodes + n_unvisited_edges
    tree_size = n_total_edges+n_total_nodes

    if print_debug: 
        print("::::::::::::")
        print(f"Total # nodes + edges: {n_total_edges + n_total_nodes}")
        print(f"Visited (n/e): {n_visited_nodes} / {n_visited_edges}")
        print(f"Unvisited (n/e): {n_unvisited_nodes} / {n_unvisited_edges}")
        print("::::::::::::")

    return (visit / (unvisit+1)) * tree_size

    # n_unvisited = (n_total_nodes - n_visited_nodes) + (n_total_edges - n_visited_edges)
    # return n_visited_nodes + n_visited_edges - n_unvisited*1


def evolve(config_file: str):
    # Create argparser with boolean flag for rendering
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--render", action="store_true", help="Render the simulation")
    parser.add_argument("-g", "--generations", type=int, default=1000, help='Number of generations to evolve for')
    parser.add_argument("-e", "--edge_coin", type=float, default=0.5, help='Probability of mutating an edge')
    parser.add_argument("-n", "--node_coin", type=float, default=0.5, help='Probability of mutating an node')
    parser.add_argument("-i", "--instance_coin", type=float, default=0.5, help='Probability of adding or removing an entity instance')
    args = parser.parse_args()

    best_ind = None
    best_score = -math.inf

    ind = EvoIndividual(config_file, args.render)
    ind.init_random_fortress()

    generation = 0

    best_score_history = []
    cur_score_history = []
    entity_num_history = []

    # while best_score < ind.max_score:
    while generation < args.generations:

        # mutate randomly
        edge_rando = random.random()
        node_rando = random.random()
        instance_rando = random.random()

        while edge_rando < args.edge_coin:
            ind.mutateFSMEdges()
            edge_rando = random.random()
        
        while node_rando < args.node_coin:
            ind.mutateFSMNodes()
            node_rando = random.random()

        while instance_rando < args.instance_coin:
            ind.mutateEnt()
            instance_rando = random.random()

        ind.simulate_fortress(generation)

        if ind.score >= best_score:
            print(f'+++ New best score! {ind.score} - generation = {generation} +++')

            if ind.fitness_type == "M":
                print("=====   M   ======")
                print(ind.engine.fortress.CHARACTER_DICT['M'].printTree())
                print("")

            best_score = ind.score
            best_ind = ind.clone()
        
        # print the stats of the generation
        print(f"[ GENERATION {generation} ]")
        print(f'> Current fortress score: {ind.score}')
        print(f'> Best fortress score: {best_score}')
        print(f"> Total entities: {len(ind.engine.fortress.entities)}")
        print("")

        # add to the histories
        best_score_history.append(best_score)
        cur_score_history.append(ind.score)
        entity_num_history.append(len(ind.engine.fortress.entities))


        ind = best_ind.clone()
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

    # export the log
    best_ind.engine.exportLog(f"LOGS/hillclimber_{best_ind.fitness_type}_[{best_ind.engine.seed}].txt")

    # export the evo individual as a pickle
    best_ind.expEvoInd(f"EVO_IND/hillclimber_{best_ind.fitness_type}_f-{best_score:.2f}_[{best_ind.engine.seed}].pkl")

    # export the histories to a matplotlib graph
    plt.figure(figsize=(15,10))
    plt.plot(best_score_history, label="Best Score", color="red")
    plt.plot(cur_score_history, label="Current Score", color="orange")
    plt.plot(entity_num_history, label="Entity Count", color="green")
    plt.legend()
    plt.savefig(f"EVO_FIT/hillclimber_{best_ind.fitness_type}_[n-{args.node_coin},e-{args.edge_coin},i-{args.instance_coin}]_s[{best_ind.engine.seed}].png")



if __name__ == '__main__':
    # Create argparser with boolean flag for rendering
    conf_file = "CONFIGS/beta_config.yaml"
    evolve(conf_file)
    # cProfile.run("evolve(conf_file)")
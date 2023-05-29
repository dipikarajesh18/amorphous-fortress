"""Evolve fortress configurations to maximize the complexity of entities' finite state machines."""
import copy
import curses
import random
import sys
import pickle

import argparse
import numpy as np

from engine import Engine
from entities import Entity
# from main import curses_render_loop, init_screens, DEBUG
from utils import newID

# NOTE: Need to turn off `DEBUG` in `main.py` lest curses interfere with printouts.

class EvoIndividual():
    n_sim_steps = 10

    def __init__(self, config_file: str, render: bool = False):
        self.config_file = config_file
        self.score = None
        engine = Engine(config_file)
        self.engine = engine
        self.render = render

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
        for node in ent.NODE_DICT.keys():
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
            

    def simulate_fortress(self):
        """Reset and simulate the fortress."""
        self.engine.resetFortress()

        # if self.render:
        #     screen_set, screen_dims = init_screens()

        loops = 0
        while not (self.engine.fortress.terminate() or self.engine.fortress.inactive() or \
                   self.engine.fortress.overpop() or loops >= self.n_sim_steps):
            # print(self.engine.fortress.renderEntities())
            self.engine.update()
            # if self.render:
            #     curses_render_loop(screen_set, screen_dims, self.engine)
            # print(loops)
            loops+=1

        if self.render:
            curses.endwin()

        print(self.engine.fortress.renderEntities())
        self.score = compute_fortress_score_dummy(self.engine)

    # export the evo individual to a file as pickle to reload object
    def expEvoInd(self, filename):
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    # import the evo individual from a file as pickle to reload object
    def impEvoInd(self, filename):
        with open(filename, 'rb') as input:
            self = pickle.load(input)




def compute_fortress_score_dummy(engine: Engine):
    """Compute the score of a fortress."""
    score = 0
    for ent in engine.fortress.entities.values():
        score += ent.char == 'M'
    return score


def evolve(config_file: str):
    # Create argparser with boolean flag for rendering
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--render", action="store_true", help="Render the simulation")
    parser.add_argument("-e", "--edge_coin", type=float, default=0.5, help='Probability of mutating an edge')
    parser.add_argument("-n", "--node_coin", type=float, default=0.5, help='Probability of mutating an node')
    args = parser.parse_args()

    best_ind = None
    best_score = -1

    ind = EvoIndividual(config_file, args.render)
    ind.init_random_fortress()

    generation = 0

    while best_score < ((ind.engine.fortress.width-2) * (ind.engine.fortress.height-2)):

        # for _ in range(3):
            # ind.mutate()

        # mutate randomly
        edge_rando = random.random()
        node_rando = random.random()

        while edge_rando < args.edge_coin:
            ind.mutateFSMEdges()
            edge_rando = random.random()
        
        while node_rando < args.node_coin:
            ind.mutateFSMNodes()
            node_rando = random.random()

        # print(f'Random number: {random.random()}')

        # end_state = None
        # while True:
        ind.simulate_fortress()
            # new_end_state = ind.engine.fortress.renderEntities()
            # if end_state is None:
            #     end_state = new_end_state
            # else:
            #     assert end_state == new_end_state

        # show cause of termination
        # END_CAUSE = engine.fortress.end_cause
        # engine.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")
        # engine.fortress.log.append(f"\n{engine.init_ent_str}")

        if ind.score >= best_score:
            print('+++ New best score! +++')
            print("=====   M   ======")
            print(ind.engine.fortress.CHARACTER_DICT['M'].printTree())
            print("")

            best_score = ind.score
            best_ind = ind.clone()
        
        print(f"[ GENERATION {generation}]")
        print(f'Current fortress score: {ind.score}')
        print(f'Best fortress score: {best_score}')

        ind = best_ind.clone()
        generation+=1


if __name__ == '__main__':
    # Create argparser with boolean flag for rendering
    conf_file = "CONFIGS/beta_config.yaml"
    evolve(conf_file)
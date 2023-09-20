import copy
import curses
import pickle
import random
import time
from engine import Engine
from render_curses import curses_render_loop, init_screens


class EvoIndividual():
    engine: Engine

    def __init__(self, config_file: str, fitness_type: str, render: bool = False):
        self.config_file = config_file
        self.score = None
        engine = Engine(config_file)
        self.engine = engine
        self.render = render

        self.n_sim_steps = 20
        self.fitness_type = fitness_type

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
            

    def simulate_fortress(self, show_prints=False, map_elites=False):
        """Reset and simulate the fortress."""
        self.engine.resetFortress()

        self.init_fortress_str = self.engine.fortress.renderEntities()

        if self.render:
            screen_set, screen_dims = init_screens()

        loops = 0
        while not (self.engine.fortress.terminate() or self.engine.fortress.inactive() or \
                   self.engine.fortress.overpop() or loops >= self.n_sim_steps):
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

        if not map_elites:
            if self.fitness_type == "M":
                self.score = compute_fortress_score_dummy(self.engine)
            elif self.fitness_type == "tree":
                self.score = compute_fortress_score(self.engine, show_prints)
        elif map_elites:
            if self.fitness_type == "M":
                score = compute_fortress_score_dummy(self.engine)
                bc_0 = len(self.engine.fortress.entities)
                bc_1 = len([e for e in self.engine.fortress.entities.values() if e.char == '@'])
            elif self.fitness_type == "tree":
                score, bc_0, bc_1 = compute_fortress_fit_bcs(self.engine, show_prints)
            self.score, self.bcs = score, (bc_0, bc_1)

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
            bc_0_bounds = (0, self.engine.fortress.max_entities)
            max_aggregate_fsm_nodes = self.engine.fortress.get_max_aggregate_fsm_nodes()
            bc_1_bounds = (0, max_aggregate_fsm_nodes)
        return (bc_0_bounds, bc_1_bounds)


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


def compute_fortress_fit_bcs(engine: Engine, print_debug=False):
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

    score = (visit / (unvisit+1))
    bc_0 = len(engine.fortress.entities)
    bc_1 = n_total_nodes
    return score, bc_0, bc_1


def mutate_ind(ind: EvoIndividual, args):
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


def mutate_and_eval_ind(ind: EvoIndividual, generation: int, args):
    mutate_ind(ind, args)
    show_prints = generation % 25 == 0
    ind.simulate_fortress(show_prints=show_prints)
    return ind


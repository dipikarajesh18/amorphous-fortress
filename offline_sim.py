# simulates a fortress from a definition file
# Usage: python offline_sim.py [fortress_def_filename] (exportFile?) (alternate_export_label)

import sys
import random
import numpy as np
import argparse

from engine import Engine
from fortress import Fortress
from entities import Entity


# shows the fortress initialization and steps in between
def showFortress(filename, seed, n_sim_steps=100, show_step=20, toFile=False,label=None):
    # ----- SETUP ----- #

    # make the engine
    ENGINE = Engine("configs/gamma_config.yaml")
    ENGINE.seed = seed;
    np.random.seed(seed)
    random.seed(seed)

    # import the fortress and populate randomly
    ENGINE.fortress.importEntityFortDef(filename)
    # print(ENGINE.fortress.CHARACTER_DICT)
    # ENGINE.populateFortress(make_char=False)

    # ----- SIMULATION ----- #

    fort_str = f"{filename} - SEED: {seed} - SIM_NUM : {n_sim_steps}\n\n"

    # print the initial state
    fort_str += "> GENERATION: 0\n"
    fort_str += ENGINE.fortress.renderEntities()
    fort_str += "\n\n"

    # simulate 
    loops = 0
    while not (ENGINE.fortress.terminate() or ENGINE.fortress.inactive() or \
                ENGINE.fortress.overpop() or loops >= n_sim_steps):
        loops+=1
        ENGINE.update(True)
        if(loops % show_step == 0):
            fort_str += f"> GENERATION {loops}\n"
            fort_str += ENGINE.fortress.renderEntities()
            fort_str += "\n\n"

    # show the number of entities total and initial fortress definition
    fort_str += f"Number of entities: {len(ENGINE.fortress.entities.keys())}\n"
    fort_str += "\n\n===============\n\n"
    fort_str += ENGINE.init_ent_str

    # show the character visit tree
    ENGINE.fortress.log.append(f"\n++++  TREE COVERAGE  ++++\n")
    for c, k in ENGINE.fortress.CHAR_VISIT_TREE.items():
        ENGINE.fortress.log.append(f"\n{c}")
        ent = ENGINE.fortress.CHARACTER_DICT[c]

        prob_n = len(k['nodes'])/len(ent.nodes) if len(ent.nodes) > 0 else 0
        prob_e = len(k['edges'])/len(ent.edges) if len(ent.edges) > 0 else 0

        ENGINE.fortress.log.append(f"Nodes: {len(k['nodes'])} / {len(ent.nodes)} = {prob_n:.2f}")
        ENGINE.fortress.log.append(f"Edges: {len(k['edges'])} / {len(ent.edges)} = {prob_e:.2f}")
        v_nodes = [ent.nodes[i] for i in k['nodes']]
        v_edges = [ent.edges[i] for i in k['edges']]

        # show the node and edges visited
        ENGINE.fortress.log.append(f"NODE SET: {v_nodes}")
        ENGINE.fortress.log.append(f"EDGE SET: {v_edges}")

    # join the log
    fort_str += "\n".join(ENGINE.fortress.log)

    # ----- EXPORT ----- #

    # print to file if asked
    if(toFile):
        alt_file = filename.split("/")[-1].replace(".txt","_SIM.txt")
        print(alt_file)
        fort_file = (f"{alt_file}" if label == None else f"{label}")
        with open(fort_file, "w+") as f:
            f.write(fort_str)
    # otherwise print to terminal
    else:   
        print(fort_str)
        
    return fort_str

if __name__ == "__main__":
    # set up the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fortress", type=str, default="FORTS/fortress.txt", help='Path to fortress definition file')
    parser.add_argument("-s", "--seed", type=int, default=1, help='Random seed')
    parser.add_argument("-n", "--n_sim_steps", type=int, default=100, help='Number of simulation steps')
    parser.add_argument("-p", "--show_step", type=int, default=20, help='Number of steps between prints')
    parser.add_argument("-e", "--export", action="store_true", help="Export to file")
    parser.add_argument("-l", "--label", type=str, default=None, help="Alternate label for export file")

    a = parser.parse_args()
    showFortress(a.fortress,a.seed,a.n_sim_steps,a.show_step,toFile=a.export,label=a.label)
    
import sys
import random
import numpy as np

from engine import Engine
from fortress import Fortress
from entities import Entity

SEED = "any"
reportFile = "_REPORT-exp1_arx.txt"

# shows the fortress initialization and steps in between
def showFortress(i,filename, seed, n_sim_steps=100, show_step=100, toFile=False,label=None):
    # ----- SETUP ----- #

    # make the engine
    ENGINE = Engine("configs/gamma_config.yaml")
    ENGINE.seed = seed;
    np.random.seed(seed)
    random.seed(seed)

    # import the fortress and populate randomly
    ENGINE.fortress.importEntityFortDef(filename)
    # print(ENGINE.fortress.CHARACTER_DICT)
    ENGINE.populateFortress(make_char=False)

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


    fort_str += f"Number of entities: {len(ENGINE.fortress.entities.keys())}\n"
    fort_str += "\n\n===============\n\n"
    fort_str += ENGINE.init_ent_str

    # ----- EXPORT ----- #

    # print to file if asked
    if(toFile):
        alt_file = filename.split("/")[-1].replace(".txt","_SIM.txt")
        fort_file = f"ELITE_FORT_SIM/" + (f"{i}--{alt_file}" if label == None else f"{label}.txt")
        with open(fort_file, "w+") as f:
            f.write(fort_str)
        
    return fort_str



def run():
    # import from command line or use the report file
    files = sys.argv[2:]
    if len(files) == 0:
        files = []
        with open(reportFile, "r") as rf:
            lines = rf.readlines()
            for l in lines[1:]:
                files.append(l.split("=> ")[-1].strip())

    print(files)

    
    i = 0
    labels = ["high_fit","high_num_ent","low_num_ent","high_num_nodes","low_num_nodes", "high_num_ent-low_num_nodes", "low_num_ent-high_num_nodes"]
    for f in files:
        s = random.randint(0,1000000) if SEED == "any" else SEED
        out_fort = showFortress(i,f,s,show_step=20,toFile=True,label=labels[i])
        i+=1
        # print(out_fort)


run()
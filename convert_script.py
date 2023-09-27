import os
import pickle
import numpy as np
from evo_utils import EvoIndividual

def convert_pkl_to_txt_def():
    
    # get all archive pkl files in saves directory
    archive_files = []
    for root, dirs, files in os.walk("saves"):
        for file in files:
            if file.endswith(".pkl"):
                archive_files.append(os.path.join(root, file))
                               
    for archive_path in archive_files:
        
        # load each archive pkl file
        with open(archive_path , 'rb') as f:
            archive = pickle.load(f)
            archive_name = archive_path.split("/")[-1].split(".")[0]
        
            # get all valid (not None) individuals 
            valid_xys = np.argwhere(archive != None)
            valid_inds = [archive[xy[0], xy[1]] for xy in valid_xys]
            ind: EvoIndividual

            # write each individual to a txt file
            for ind in valid_inds:
                output_filepath = f"ind-character-def/{archive_name}_[{str(ind.bc_sim_vals[0])}, {str(ind.bc_sim_vals[1])}]_f{ind.score}.txt"
                f = open(output_filepath, "w")
                f.write(ind.engine.init_ent_str)

if __name__ == "__main__":
    convert_pkl_to_txt_def()
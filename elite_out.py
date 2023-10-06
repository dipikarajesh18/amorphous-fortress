import os
import pickle
import numpy as np
from tqdm import tqdm
from evo_utils import EvoIndividual

OUTPUT_FOLDER = "ELITE_CHAR_DEF"
SAVE_FOLDER = "archive_pickles"


# report saving - format is the value followed by filename
highest_fitness = []
highest_x = []
lowest_x = []
highest_y = []
lowest_y = []
high_x_low_y = []
low_x_high_y = []

def convert_pkl_to_txt_def():

    # get all archive pkl files in saves directory
    archive_files = []
    for root, dirs, files in os.walk(SAVE_FOLDER):
        for file in files:
            if file.endswith(".pkl"):
                archive_files.append(os.path.join(root, file))

          
    for archive_path in archive_files:
        
        # load each archive pkl file
        archive_name = ""
        with open(archive_path , 'rb') as f:
            archive = pickle.load(f)
            archive_name = archive_path.split("/")[-1].split(".")[0]
        
            # get all valid (not None) individuals 
            valid_xys = np.argwhere(archive != None)
            valid_inds = [archive[xy[0], xy[1]] for xy in valid_xys]
            ind: EvoIndividual

            # save the best in each cell based on setup

            # write each individual to a txt file
            with tqdm(total=(len(valid_inds))) as pbar:         
                for ind in valid_inds:
                    output_filepath = f"{OUTPUT_FOLDER}/{archive_name}_f[{ind.score:.3f}]_xy[{ind.bc_sim_vals[0]:.3f}, {ind.bc_sim_vals[1]:.3f}].txt"
                    f = open(output_filepath, "w")
                    f.write(ind.engine.init_ent_str)

                    # check against the superlatives
                    isBest(ind,output_filepath)

                    pbar.update(1);

        
        # print a report for the filename for the highest and lowest of each 
        with open(f"_REPORT-{archive_name}.txt", "w+") as rpt:
            report = "== REPORT ==\n"
            report += f"Best fitness = [{highest_fitness[0]:.4f}] => {highest_fitness[1]}\n"
            report += f"Highest X = [{highest_x[0]:.4f}] => {highest_x[1]}\n"
            report += f"Lowest X = [{lowest_x[0]:.4f}] => {lowest_x[1]}\n"
            report += f"Highest Y = [{highest_y[0]:.4f}] => {highest_y[1]}\n"
            report += f"Lowest Y = [{lowest_y[0]:.4f}] => {lowest_y[1]}\n"
            report += f"Highest X Lowest Y = [{high_x_low_y[0]:.4f}] [{high_x_low_y[1]}] => {high_x_low_y[2]}\n"
            report += f"Lowest X Highest Y = [{low_x_high_y[0]:.4f}] [{low_x_high_y[1]}] => {low_x_high_y[2]}\n"

            rpt.write(report)


# check if it has the highest or lowest of something so far
def isBest(i,f):
    global highest_fitness, highest_x, highest_y, lowest_x, lowest_y, low_x_high_y, high_x_low_y

    # check fitness
    if len(highest_fitness) == 0 or i.score > highest_fitness[0]:
        highest_fitness = [i.score,f]

    # check x axis BC
    if len(highest_x) == 0 or i.bc_sim_vals[0] > highest_x[0]:
        highest_x = [i.bc_sim_vals[0], f]
    elif len(lowest_x) == 0 or i.bc_sim_vals[0] < lowest_x[0]:
        lowest_x = [i.bc_sim_vals[0], f]

    # check y axis BC
    if len(highest_y) == 0 or i.bc_sim_vals[1] > highest_y[0]:
        highest_y = [i.bc_sim_vals[1], f]
    elif len(lowest_y) == 0 or i.bc_sim_vals[1] < lowest_y[0]:
        lowest_y = [i.bc_sim_vals[1], f]

    # check low x high y
    if (len(low_x_high_y) == 0) or (i.bc_sim_vals[0] < low_x_high_y[0] and i.bc_sim_vals[1] > low_x_high_y[1]):
        low_x_high_y = [i.bc_sim_vals[0], i.bc_sim_vals[1], f]
    
    # check high x low y
    if (len(high_x_low_y) == 0) or (i.bc_sim_vals[0] > high_x_low_y[0] and i.bc_sim_vals[1] < high_x_low_y[1]):
        high_x_low_y = [i.bc_sim_vals[0], i.bc_sim_vals[1], f]

if __name__ == "__main__":
    convert_pkl_to_txt_def()
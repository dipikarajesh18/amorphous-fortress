import sys
import random
import numpy as np
import argparse
import glob

from engine import Engine
from fortress import Fortress
from entities import Entity

from offline_sim import showFortress



if __name__ == "__main__":

    # set up the argument parser
    el_parser = argparse.ArgumentParser()
    el_parser.add_argument("-x", "--x_pos", type=str, default="30", help='X position in the archive ("*_xy[[X_POS,Y_POS]])_*"); allows wildcard characters')
    el_parser.add_argument("-y", "--y_pos", type=str, default="70", help='Y position in the archive ("*_xy[[X_POS,Y_POS]])_*"); allows wildcard characters')
    el_parser.add_argument("-a", "--archive", type=str, default="QD_EXP/ELITE_CHAR_DEF", help='Path to the archive')
    el_parser.add_argument("-r", "--report", type=str, default=None, help='Path to the report file')
    el_parser.add_argument("-s", "--seed", type=int, default=-1, help='Random seed')
    el_parser.add_argument("-n", "--n_sim_steps", type=int, default=100, help='Number of simulation steps')
    el_parser.add_argument("-p", "--show_step", type=int, default=20, help='Number of steps between prints')
    el_parser.add_argument("-e", "--export", action="store_true", help="Export to file")


    args = el_parser.parse_args()
    labels = []
    files = []
    # use report files
    if args.report is not None:
        print(">> USING REPORT DATA")
        with open(args.report, "r") as rf:
            lines = rf.readlines()
            for l in lines[1:]:
                files.append(l.split("=> ")[-1].strip())
        labels = ["high_fit.txt","high_num_ent.txt","low_num_ent.txt","high_num_nodes.txt","low_num_nodes.txt", "high_num_ent-low_num_nodes.txt", "low_num_ent-high_num_nodes.txt"]
    # use specified archive files
    else:
        print(f">> USING ARCHIVE DATA from {args.archive}")
        x_pos = args.x_pos
        y_pos = args.y_pos
        print(x_pos,y_pos)

        # get the files using glob
        files = glob.glob(f"{args.archive}/*_xy[[][[]{x_pos}_{y_pos}[]][]]*")
        # files = glob.glob(args.archive+'/*_xy[[][[]*[]][]]*') 

    print(files)
    
    i = 0
    for f in files:
        s = random.randint(0,1000000) if args.seed == -1 else args.seed
        showFortress(f,s,n_sim_steps=args.n_sim_steps,show_step=args.show_step,toFile=args.export,label=None if len(labels) == 0 else labels[i])
        i+=1
        # print(out_fort)


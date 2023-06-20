#!/bin/bash

python evolve.py -c ALIFE_EXP/exp1.yaml -g 1000 -e 0.5 -n 0.5 -i 0.5 -a &> exp1_out.txt
python evolve.py -c ALIFE_EXP/exp2.yaml -g 1000 -e 0.5 -n 0.5 -i 0.5 -a &> exp2_out.txt
python evolve.py -c ALIFE_EXP/exp3.yaml -g 1000 -e 0.5 -n 0.5 -i 0.5 -a &> exp3_out.txt
python evolve.py -c ALIFE_EXP/exp4.yaml -g 1000 -e 0.5 -n 0.5 -i 0.5 -a &> exp4_out.txt
python evolve.py -c ALIFE_EXP/exp5.yaml -g 1000 -e 0.5 -n 0.5 -i 0.5 -a &> exp5_out.txt
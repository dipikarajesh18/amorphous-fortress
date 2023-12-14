# amorphous-fortress



## 0. Table of Contents

1. [Realtime Simulation](#1-realtime-simulation)
2. [Offline Simulation](#2-offline-simulation)
3. [Authors and Contributors](#3-authors-and-contributors)
4. [Paper Publications](#4-paper-publications)


## 1. Real-Time Simulation
This code allows you to see the fortress run in real time through the terminal using `curses`. Recommended to use a fullscreen terminal.

### 1.1. Quick run
`python main.py`

`python main.py -t KOROK  # runs the korok example`

`python main.py -f FORTS/HYRULE.txt   # imports the hyrule fortress`

#### 1.2. Arguments

`-t --test` - The test environment to use [DUCK, AMOEBA, GRASS, BOKO, GORON, KOROK, BLUPEE, POKEMON] (see below)
`-f --fortress_file` - Path to a defined fortress file to import
`-s --seed` - Seed to use for the fortress
`-d --debug` - In debug mode, doesn't show curses interface
`-c --config` - Configuration file to use for the simulation

**TESTS (populated by premade entities in ENT/)**
- DUCK => test movement nodes
- AMOEBA => test take nodes
- GRASS => test die nodes
- BOKO => test chase nodes
- GORON => test push nodes
- BLUPEE => test add nodes
- KOROK => test transform nodes
- POKEMON => test move_wall nodes

## 2. Offline Simulation
Simulates an exported fortress file all at once with a specific seed and saves the output


### 2.1. Quick run
`python offline_sim.py [ARGS]`

`python offline_sim.py -f FORTS/HYRULE.txt   # simulates the HYRULE fortress`

### 2.2 Arguments

`-f --fortress` - Path to fortress definition file

`-s --seed` - Random seed

`-n --n_sim_steps` - Number of simulation steps

`-p --show_step` - Number of steps between prints
 
`-e --export` - Export to file

`-l --label` - Alternate label for export file


### 2.3 QD Archive Setup (Optional)
1. Download the [ELITE_CHAR_DEF](https://drive.google.com/file/d/1y4LSOpBvCc83slGmH5WgFdp72MlPmxCA/view?usp=sharing) set and extract the folder to the [QD_EXP](QD_EXP/) folder.
   - NOTE: This contains all of the archived QD fortress definitions for each cell including FSM class definitions, initial placement, and map layout. These files are labeled by `exp1_f[FORTRESS FITNESS]_xy[[X_Y ARCHIVE POSITION]]-[X_Y ARCHIVE VALUES].txt`
2. Run the [elite_fort_viewer.py](elite_fort_viewer) with the X and Y inputs as the specified x,y dimension index for the archive cells. Wildcard characters are also accepted.
   - Ex. `python elite_fort_viewer.py -x 70 -y 12` will simulate the 'QD_EXP/ELITE_CHAR_DEF/exp1_f[0.354]_xy[[70_12]]-[111.400,198.000].txt' file
   - Ex. `python elite_fort_viewer.py -x ? -y ?` will simulate all files with single digits in both dimensions (i.e. x=[0-9] y=[0-9])

## 3. Authors and Contributors
M Charity, Sam Earle, Dipika Rajesh, Mayu Wilson

## 4. Paper Publications
- [Amorphous Fortress: Observing Emergent Behavior in Multi-Agent FSMs](https://arxiv.org/pdf/2306.13169.pdf) (ALIFE for and from games workshop 2023)
- [Quality Diversity in the Amorphous Fortress (QD-AF): Evolving for Complexity in 0-Player Games](https://arxiv.org/abs/2312.02231) (NeurIPS ALOE Workshop 2023)
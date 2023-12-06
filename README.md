# amorphous-fortress



## 0. Table of Contents

1. [Realtime Simulation](#1-realtime-simulation)



## 1. Real-Time Simulation
This code allows you to see the fortress run in real time through the terminal using `curses`

### 1.1. Quick run
`python main.py [CONFIG_FILE] [TEST_TYPE]`

`python main.py CONFIGS/gamma_config.yaml KOROK  # runs the korok example`

#### 1.2. Main Parameters

**CONFIG (found in CONFIGS/)**
- alpha_config => basic interactions 
- beta_config => most interaction spaces
- *gamma_config => all interaction spaces and faster simulation speed

\* preferred use


**TESTS (populated by premade entities in ENT/)**
- DUCK => test movement nodes
- AMOEBA => test take nodes
- GRASS => test die nodes
- BOKO => test chase nodes
- GORON => test push nodes
- BLUPEE => test add nodes
- KOROK => test transform nodes
- POKEMON => test move_wall nodes

## 2. Logged Simulation
Simulates an exported fortress file with a specific seed and saves the output


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

## 3. Authors and Contributors
M Charity
Sam Earle
Dipika Rajesh
Mayu Wilson

## 4. Paper Publications
- [Amorphous Fortress: Observing Emergent Behavior in Multi-Agent FSMs](https://arxiv.org/pdf/2306.13169.pdf) (ALIFE for and from games workshop 2023)
- [Quality Diversity in the Amorphous Fortress (QD-AF): Evolving for Complexity in 0-Player Games](https://arxiv.org/abs/2312.02231) (NeurIPS ALOE Workshop 2023)
import curses
import time
import random
import numpy as np

from engine import Engine
from fortress import Fortress
from entities import Entity

DEBUG = False   # shows in curses
ENGINE = None   # the engine
TEST = ""       # test a specific setup

# Initialize the screen
if not DEBUG:
    SCREEN = curses.initscr()
    curses.curs_set(0)
    SCREEN.clear()
    curses.start_color()

    curs_colors = [curses.COLOR_RED,curses.COLOR_YELLOW,curses.COLOR_BLUE,curses.COLOR_CYAN,curses.COLOR_GREEN,curses.COLOR_MAGENTA, curses.COLOR_WHITE]
    for i in range(len(curs_colors)):
        curses.init_pair(i+1,curs_colors[i],curses.COLOR_BLACK)
    COLORS = {
        'RED': 1,
        'YELLOW': 2,
        'BLUE': 3,
        'CYAN': 4,
        'GREEN': 5,
        'MAGENTA': 6,
        'WHITE': 7
    }

# setup the terminal screens 
def init_screens():

    # Get the screen dimensions
    screen_height, screen_width = SCREEN.getmaxyx()

    # Calculate the width for the sim screen, log screen, and tree screen
    sim_width = screen_width // 2
    log_width = screen_width // 2
    tree_width = screen_width - sim_width

    sim_height = (screen_height - 1) // 2
    log_height = (screen_height - 1) // 2
    tree_height = screen_height - 1


    # Create the simulation window
    sim_window = curses.newwin(sim_height, sim_width, 0, 0)
    sim_window.keypad(True)
    sim_window.nodelay(True)  # Enable non-blocking input

    # Create the log window
    log_window = curses.newwin(log_height, log_width, sim_height, 0)

    # Create the tree window
    tree_window = curses.newwin(tree_height, tree_width, 0, sim_width)

    # return all the new windows
    return [sim_window, log_window, tree_window], [sim_height, sim_width, log_height, log_width, tree_height, tree_width]


# the update loop for the simulation
def curses_render_loop(screen_set, screen_dims, engine):
    sim, log, tree = screen_set  # unpack the screen set
    sim_height, sim_width, log_height, log_width, tree_height, tree_width = screen_dims  # unpack the screen dimensions

    # Clear all of the windows every time
    sim.erase()
    log.erase()
    tree.erase()

    # add the title screen and timestep
    title_text = f"====== DUCK FORTRESS [{engine.seed}] ======"
    sim.addstr(0, sim_width//2-len(title_text)//2, title_text)

    time_text = f"Timestep: {engine.sim_tick}"
    sim.addstr(2, sim_width//2-len(time_text)//2, time_text)


    # draw the fortress environment from the engine
    fortmap = engine.fortress.renderEntities()
    fortmapChar = [c for r in fortmap for c in r]
    row_length = fortmap.index('\n')
    col_length = fortmap.count('\n')
    sx = max(0,sim_width//2 - row_length//2)
    sy = max(0,sim_height//2 - col_length//2)
    
    y = 0
    x = 0
    for c in fortmapChar:
        if c == "\n":
            y += 1
            x = 0
            continue
        sim.addch(y+sy, x+sx, c)
        x += 1



    # draw the log window
    title_text = f"=============    LOG    ============="
    log.addstr(1, log_width//2-len(title_text)//2, title_text)

    # add log elements based on the amount of rows in the log window
    num_log_rows = log_height - 3
    show_lines = min(len(engine.fortress.log),num_log_rows)
    digit_off = len(str(len(engine.fortress.log)))
    for li in range(show_lines):
        cur_log = engine.fortress.log[-show_lines:]
        line_index = str(li+(len(engine.fortress.log)-show_lines)).rjust(digit_off, " ")
        log.addstr(li+3, 1, f"{line_index}: {cur_log[li]}")
 


    # draw the tree window
    # just use a sample tree for now lol

    # add a border?
    for i in range(tree_height):
        tree.addch(i, 0, "|")
        # tree.addch(i, tree_width-1, "|")

    ent_txt = "======= ENTITY TREE ======="
    tree.addstr(0, tree_width//2-len(ent_txt)//2, ent_txt)
    num_entities = len(engine.fortress.entities)

    cur_line = 0
    offY = 2
    offX = 3
    ent_list = list(engine.fortress.entities.values())
    for i in range(num_entities):
        ent = ent_list[i]
        entTree = ent.printTree()
        entTree_lines = entTree.split("\n")
        entTree_lines = [l for l in entTree_lines if l != ""]
        for j in range(len(entTree_lines)):

            # highlight the character (add id and position)
            if j == 0:
                tree.addstr(offY+cur_line, offX, f"{ent.char}.{ent.id} ({ent.pos})", curses.color_pair(COLORS['RED']))
            # highlight current node
            elif entTree_lines[j].split(":")[0] == str(ent.cur_node):
                tree.addstr(offY+cur_line, offX, entTree_lines[j], curses.color_pair(COLORS['CYAN']))
            # highlight the current edge (if there is one)
            elif ent.moved_edge and entTree_lines[j].split(":")[0] == ent.moved_edge:
                tree.addstr(offY+cur_line, offX, entTree_lines[j], curses.color_pair(COLORS['GREEN']))
            # write everything else
            else:
                tree.addstr(offY+cur_line, offX, entTree_lines[j], curses.color_pair(COLORS['WHITE']))
            cur_line += 1
        cur_line += 1

        if cur_line >= tree_height or (i<(num_entities-1) and cur_line+len(ent_list[i+1].printTree().split('\n')) >= tree_height):
            cur_line = 0
            offX += 20

            # not enough room to draw the next entity
            if offX > tree_width-20: 
                break


    # refresh all the windows
    sim.refresh()
    log.refresh()
    tree.refresh()


# main function
def main():
    global ENGINE

    # setup the engine
    ENGINE = Engine()
    np.random.seed(ENGINE.seed)
    random.seed(ENGINE.seed)

    # setup the screens
    if not DEBUG:
        screen_set, screen_dims = init_screens()


    # add entities based on preset or at random
    if TEST == "DUCK":
        ent = Entity(ENGINE.fortress, filename="ENT/duck.txt")
        ent.pos = [3,3]
        ENGINE.fortress.addEntity(ent)

    elif TEST == "AMOEBA":
        a1 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a1.pos = [3,3]
        ENGINE.fortress.addEntity(a1)

        a2 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a2.pos = [7,6]
        ENGINE.fortress.addEntity(a2)

        a3 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a3.pos = [3,3]
        ENGINE.fortress.addEntity(a3)

    elif TEST == "GRASS":
        # get 10 random positions
        # cannot just do random positions since the seed call will return the same value every time
        rposx = np.random.randint(1,ENGINE.fortress.width-1,10)
        rposy = np.random.randint(1,ENGINE.fortress.height-1,10)

        for i in range(10):
            ent = Entity(ENGINE.fortress, filename="ENT/grass.txt")
            ent.pos = [rposx[i], rposy[i]]
            ENGINE.fortress.addEntity(ent)
    else:
        ENGINE.populateFortress()

    # run the update loop
    if not DEBUG:
        loops = 0
        while not ENGINE.fortress.terminate() and not ENGINE.fortress.inactive():
            ENGINE.update()
            curses_render_loop(screen_set, screen_dims, ENGINE)
            time.sleep(ENGINE.config['sim_speed'])

            # that swan's coming thomas.... kill it. RAAAARRRR!
            # if loops == 0:
            #     ENGINE.fortress.removeFromMap(ent)
            loops+=1

    # show cause of termination
    END_CAUSE = ENGINE.fortress.end_cause
    ENGINE.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")

    # End the simulation
    if not DEBUG:
        curses.endwin()
        if ENGINE.config['save_log'] and ENGINE.config['min_log'] <= len(ENGINE.fortress.log):
            ENGINE.exportLog(ENGINE.config['log_file'].replace("<SEED>", str(ENGINE.seed)))


if __name__ == "__main__":
    try:
        main()
    # handle crashes
    except:
        curses.nocbreak()
        SCREEN.keypad(0)
        curses.echo()
        curses.endwin()

        # show cause of termination
        END_CAUSE = ENGINE.fortress.end_cause
        ENGINE.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")

        if ENGINE.config['save_log'] and ENGINE.config['min_log'] <= len(ENGINE.fortress.log):
            ENGINE.exportLog(ENGINE.config['log_file'].replace("<SEED>", str(ENGINE.seed)))

        raise
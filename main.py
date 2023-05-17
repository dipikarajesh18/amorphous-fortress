import curses
import time

from engine import Engine
from fortress import Fortress
from entities import Entity

DEBUG = False   # shows in curses

# Initialize the screen
if not DEBUG:
    SCREEN = curses.initscr()
    curses.curs_set(0)
    SCREEN.clear()

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
def update_loop(screen_set, screen_dims, engine):
    sim, log, tree = screen_set  # unpack the screen set
    sim_height, sim_width, log_height, log_width, tree_height, tree_width = screen_dims  # unpack the screen dimensions

    # Clear all of the windows every time
    sim.erase()
    log.erase()
    tree.erase()

    # draw the fortress environment from the engine
    fortmap = engine.fortress.renderEntities()
    fortmapChar = [c for r in fortmap for c in r]
    y = 0
    x = 0
    for c in fortmapChar:
        if c == "\n":
            y += 1
            x = 0
            continue
        sim.addch(y, x, c)
        x += 1

    # add a border?
    # for i in range(tree_height):
    #     tree.addch(i, 0, "|")
    #     tree.addch(i, tree_width-1, "|")


    # draw the log window
    log.addstr(1, 1, f"=== DUCK FORTRESS [{engine.seed}] ===")

    # # draw the tree window
    # # just use a sample tree for now lol

    num_entities = len(engine.fortress.entities)

    cur_line = 0
    offX = 0
    for i in range(len(engine.fortress.entities)):
        ent = engine.fortress.entities[i]
        entTree = ent.printTree()
        entTree_lines = entTree.split("\n")
        for j in range(len(entTree_lines)):
            tree.addstr(cur_line, offX, entTree_lines[j])
            cur_line += 1
        cur_line += 1

        if cur_line >= tree_height:
            cur_line = 0
            offX += 20


    # ent = Entity("@", engine.fortress)
    # entTree = ent.printTree()
    # entTree_lines = entTree.split("\n")
    # for i in range(entTree_lines):
    #     tree.addstr(i, 0, entTree_lines[i])

    # refresh all the windows
    sim.refresh()
    log.refresh()
    tree.refresh()


# main function
def main():

    # setup the screens
    screen_set, screen_dims = init_screens()

    # setup the engine
    engine = Engine()

    # add a fake entity
    ent = Entity("@", engine.fortress)
    ent.id = 1
    ent.pos = [3,3]
    engine.fortress.addEntity(ent)

    # run the update loop
    loop_once = False
    while not engine.fortress.terminate() or loop_once:
        update_loop(screen_set, screen_dims, engine)
        # engine.update()
        time.sleep(2)
        loop_once = False

    # End the simulation
    if not DEBUG:
        curses.endwin()


if __name__ == "__main__":
    try:
        main()
    # handle crashes
    except:
        curses.nocbreak()
        SCREEN.keypad(0)
        curses.echo()
        curses.endwin()
        raise
import curses

DEBUG = False   # shows in curses if FALSE
ENGINE = None   # the engine
TEST = ""       # test a specific setup

COLORS = {
    'RED': 1,
    'YELLOW': 2,
    'BLUE': 3,
    'CYAN': 4,
    'GREEN': 5,
    'MAGENTA': 6,
    'WHITE': 7
}

def init_screens():
    # Initialize the screen
    SCREEN = curses.initscr()
    curses.curs_set(0)
    SCREEN.clear()
    curses.start_color()

    curs_colors = [curses.COLOR_RED,curses.COLOR_YELLOW,curses.COLOR_BLUE,curses.COLOR_CYAN,curses.COLOR_GREEN,curses.COLOR_MAGENTA, curses.COLOR_WHITE]
    for i in range(len(curs_colors)):
        curses.init_pair(i+1,curs_colors[i],curses.COLOR_BLACK)

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
    title_text = f"====== AMORPHOUS FORTRESS [{engine.seed}] ======"
    sim.addstr(0, sim_width//2-len(title_text)//2, title_text)

    time_text = f"Timestep: {engine.sim_tick} --- # entities: {engine.fortress.max_entities} / {(engine.fortress.max_entities)}"
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

import curses
import time
import random
import numpy as np
import sys
import render_curses as render

from engine import Engine
from fortress import Fortress
from entities import Entity

DEBUG = False   # shows in curses if FALSE
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


# main functionå
def main(config_file):
    global ENGINE

    # setup the engine
    ENGINE = Engine(config_file)
    np.random.seed(ENGINE.seed)
    random.seed(ENGINE.seed)

    # setup the screens
    if not DEBUG:
        screen_set, screen_dims = render.init_screens()


    # test move
    if TEST == "DUCK":
        ent = Entity(ENGINE.fortress, filename="ENT/duck.txt")
        ent.pos = [3,3]
        ENGINE.fortress.addEntity(ent)
        ENGINE.fortress.addLog(">>> Running [DUCK] test <<<")

    # test take
    elif TEST == "AMOEBA":
        a1 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a1.pos = [3,3]
        ENGINE.fortress.addEntity(a1)

        a2 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a2.pos = [7,6]
        ENGINE.fortress.addEntity(a2)

        a3 = Entity(ENGINE.fortress, filename="ENT/amoeba.txt")
        a3.pos = [4,3]
        ENGINE.fortress.addEntity(a3)

        ENGINE.fortress.addLog(">>> Running [AMOEBA] test <<<")

    # test die
    elif TEST == "GRASS":
        # get 10 random positions
        # cannot just do random positions since the seed call will return the same value every time
        rposx = np.random.randint(1,ENGINE.fortress.width-1,10)
        rposy = np.random.randint(1,ENGINE.fortress.height-1,10)

        for i in range(10):
            ent = Entity(ENGINE.fortress, filename="ENT/grass.txt")
            ent.pos = [rposx[i], rposy[i]]
            ENGINE.fortress.addEntity(ent)

        ENGINE.fortress.addLog(">>> Running [GRASS] test <<<")

    # test chase
    elif TEST == "BOKO":
        b = Entity(ENGINE.fortress, filename="ENT/boko.txt")
        b.pos = [9,5]
        ENGINE.fortress.addEntity(b)

        l = Entity(ENGINE.fortress, filename="ENT/link.txt")
        l.pos = [2,3]
        ENGINE.fortress.addEntity(l)

        ENGINE.fortress.addLog(">>> Running [BOKO] test <<<")

    # test push
    elif TEST == "GORON":
        g = Entity(ENGINE.fortress, filename="ENT/goron.txt")
        g.pos = [2,2]
        ENGINE.fortress.addEntity(g)

        g2 = Entity(ENGINE.fortress, filename="ENT/goron.txt")
        g2.pos = [6,4]
        ENGINE.fortress.addEntity(g2)

        r = Entity(ENGINE.fortress, filename="ENT/rock.txt")
        r.pos = [5,5]
        ENGINE.fortress.addEntity(r)

        r2 = Entity(ENGINE.fortress, filename="ENT/rock.txt")
        r2.pos = [7,3]
        ENGINE.fortress.addEntity(r2)

        r3 = Entity(ENGINE.fortress, filename="ENT/rock.txt")
        r3.pos = [5,1]
        ENGINE.fortress.addEntity(r3)

        r4 = Entity(ENGINE.fortress, filename="ENT/rock.txt")
        r4.pos = [11,4]
        ENGINE.fortress.addEntity(r4)

        ENGINE.fortress.addLog(">>> Running [GORON] test <<<")

    # test add
    # TODO: do something about too many entities being stacked on top of each other
    elif TEST == "BLUPEE":
        l = Entity(ENGINE.fortress, filename="ENT/link.txt")
        l.pos = [7,3]
        ENGINE.fortress.addEntity(l)

        b = Entity(ENGINE.fortress, filename="ENT/blupee.txt")
        b.pos = [13,1]
        ENGINE.fortress.addEntity(b)

        b2 = Entity(ENGINE.fortress, filename="ENT/blupee.txt")
        b2.pos = [1,1]
        ENGINE.fortress.addEntity(b2)

        b3 = Entity(ENGINE.fortress, filename="ENT/blupee.txt")
        b3.pos = [1,6]
        ENGINE.fortress.addEntity(b3)

        b4 = Entity(ENGINE.fortress, filename="ENT/blupee.txt")
        b4.pos = [13,6]
        ENGINE.fortress.addEntity(b4)

        # add to the list to spawn later
        ENGINE.fortress.CHARACTER_DICT['$'] = Entity(ENGINE.fortress, char='$', nodes=["idle"], edges={'0-0':'none'})

        ENGINE.fortress.addLog(">>> Running [BLUPEE] test <<<")

    # test transform
    elif TEST == "KOROK":
        l = Entity(ENGINE.fortress, filename="ENT/link.txt")
        l.pos = [7,3]
        ENGINE.fortress.addEntity(l)

        k = Entity(ENGINE.fortress, filename="ENT/korok.txt")
        k.pos = [9,5]
        ENGINE.fortress.addEntity(k)

        # add to the list to spawn later
        ENGINE.fortress.CHARACTER_DICT['$'] = Entity(ENGINE.fortress, char='$', nodes=["idle"], edges={'0-0':'none'})

        ENGINE.fortress.addLog(">>> Running [KOROK] test <<<")

    # test wall
    elif TEST == "POKEMON":
        for i in range(5):
            w = Entity(ENGINE.fortress, filename="ENT/rock.txt")
            w.pos = [5+i,3]
            ENGINE.fortress.addEntity(w)
        
        t = Entity(ENGINE.fortress, filename="ENT/poke_trainer.txt")
        t.pos = [7,4]
        ENGINE.fortress.addEntity(t)

        ENGINE.fortress.addLog(">>> Running [POKEMON] test <<<")

    else:
        ENGINE.populateFortress()

    # run the update loop
    if not DEBUG:
        loops = 0
        while not (ENGINE.fortress.terminate() or ENGINE.fortress.inactive() or ENGINE.fortress.overpop()) :
            ENGINE.update()
            render.curses_render_loop(screen_set, screen_dims, ENGINE, ENGINE.config['min_view'])
            time.sleep(ENGINE.config['sim_speed'])

            # that swan's coming thomas.... kill it. RAAAARRRR!
            # if loops == 0:
            #     ENGINE.fortress.removeFromMap(ent)
            loops+=1

    # show cause of termination
    END_CAUSE = ENGINE.fortress.end_cause
    ENGINE.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")
    ENGINE.fortress.log.append(f"\n{ENGINE.init_ent_str}")

    # End the simulation
    if not DEBUG:
        curses.endwin()
        if ENGINE.config['save_log'] and ENGINE.config['min_log'] <= len(ENGINE.fortress.log):
            ENGINE.exportLog(ENGINE.config['log_file'].replace("<SEED>", str(ENGINE.seed)))


if __name__ == "__main__":

    try:
        conf_file = sys.argv[1] if len(sys.argv) > 1 else "CONFIGS/gamma_config.yaml"
        TEST = sys.argv[2] if len(sys.argv) > 2 else ""
        DEBUG = True if len(sys.argv) > 3 else False
        main(conf_file)

    # handle crashes
    except:
        curses.nocbreak()
        SCREEN.keypad(0)
        curses.echo()
        curses.endwin()

        # show cause of termination
        END_CAUSE = ENGINE.fortress.end_cause
        ENGINE.fortress.log.append(f"==== SIMULATION ENDED: {END_CAUSE} ====")
        ENGINE.fortress.log.append(f"\n{ENGINE.init_ent_str}")

        # print the trees of each entity that was at the start of the simulation

        if ENGINE.config['save_log'] and ENGINE.config['min_log'] <= len(ENGINE.fortress.log):
            ENGINE.exportLog(ENGINE.config['log_file'].replace("<SEED>", str(ENGINE.seed)))

        raise
    
    # test push
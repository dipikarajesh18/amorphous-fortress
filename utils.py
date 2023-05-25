import random


# create a new id for the entity (copied from `entities.py` but abstracted a bit so we can use it for the reference)
def newID(all_ids,id_len=4):
    all_num = list(range(16**4))
    while len(all_num) > 0:
        i = f'%{id_len}x' % random.choice(all_num)
        if i not in all_ids:
            return i
        all_num.remove(int(i,16))

    return f'%0{id_len}x' % random.randrange(16**(id_len+1))
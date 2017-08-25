LIMIT_POSITION_LIST = 20

def lr_diff(l, r):
    return list(set(l).difference(r))


def lr_intr(l, r):
    return list(set(l).intersection(r))

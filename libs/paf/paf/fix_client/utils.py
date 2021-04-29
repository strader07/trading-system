import numpy as np


def tround(val, tick_size):
    """ Round price to tick size """
    return int(np.round(val * tick_size)) / tick_size

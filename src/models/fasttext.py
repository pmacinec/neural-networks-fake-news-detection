import numpy as np
import os


def read_fasttext_model(path):
    """
    Read fasttext model from .vec file.

    :param path: str, path to model in .vec format.
    :return: dict, fasttext pre-trained word embedddings.
    """
    if not os.path.isfile(path):
        return None

    fasttext = {}
    with open(path) as file:
        for line in file.readlines():
            values = line.split()
            fasttext[values[0]] = np.asarray(values[1:], dtype='float32')

    return fasttext

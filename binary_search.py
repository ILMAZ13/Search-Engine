import sys
import numpy as np
from pymystem3 import Mystem

PATH_TO_DIR = "sites"
PATH_TO_INDEX = PATH_TO_DIR + "/index.txt"
PATH_TO_REVERSED_INDEXES = PATH_TO_DIR + "/reversed_index.txt"


def read_urls():
    paths = []
    with open(PATH_TO_INDEX) as textFile:
        for line in textFile:
            paths.append(line.split()[1])
    return paths


def read_reversed_indexes():
    indexes = {}
    with open(PATH_TO_REVERSED_INDEXES) as textFile:
        for line in textFile:
            splitted_text = line.split()
            indexes[splitted_text[0]] = splitted_text[1:]
    return indexes


if __name__ == '__main__':
    paths = read_urls()
    indexes = read_reversed_indexes()

    words_len = len(sys.argv) - 1

    if words_len == 0:
        print("No words in search")
        exit(-1)

    words = sys.argv[1:]

    zeros = np.zeros(len(paths), dtype=int)

    m = Mystem()
    lemmas = [m.lemmatize(word.lower())[0] for word in words]
    for word in lemmas:
        if word in indexes:
            for i, boo in enumerate(indexes[word]):
                zeros[i] += int(boo)
        else:
            print(word + " -- doesn't exist in dictionary")
            words_len -= 1
    print("Search results:")
    for i, num in enumerate(zeros):
        if num == words_len:
            print(paths[i])

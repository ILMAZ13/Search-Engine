import sys
import numpy as np
from pymystem3 import Mystem

PATH_TO_DIR = "sites"
PATH_TO_INDEX = PATH_TO_DIR + "/index.txt"
PATH_TO_REVERSED_INDEXES = PATH_TO_DIR + "/tf_idf.txt"


def read_urls():
    paths = []
    with open(PATH_TO_INDEX) as textFile:
        for line in textFile:
            paths.append(line.split()[1])
    return paths


def read_reversed_indexes():
    indexes = []
    tokens = []
    is_first_line = True
    with open(PATH_TO_REVERSED_INDEXES) as textFile:
        for line in textFile:
            splitted_text = line.split()
            if len(splitted_text) != 41:
                print("ALARM ", line)
            tokens.append(splitted_text[0])
            for index, tf_idf in enumerate(splitted_text[1:]):
                if is_first_line:
                    indexes.append([])
                indexes[index].append(float(tf_idf))
            is_first_line = False
    return indexes, tokens


def calculate_tf(lemmas):
    tf = {}
    doc_count = len(lemmas)
    for token in lemmas:
        tf[token] = lemmas.count(token) / doc_count
    return tf


if __name__ == '__main__':
    paths = read_urls()
    indexes, tokens = read_reversed_indexes()

    doc_vec_len = []
    for vector in indexes:
        doc_vec_len.append(np.linalg.norm(vector))

    words_len = len(sys.argv) - 1

    if words_len == 0:
        print("No words to search")
        exit(-1)

    words = sys.argv[1:]

    zeros = np.zeros(len(tokens), dtype=float)

    m = Mystem()
    lemmas = [m.lemmatize(word.lower())[0] for word in words]
    tf = calculate_tf(lemmas)
    for token in tf.keys():
        if token in tokens:
            zeros[tokens.index(token)] = tf[token]
        else:
            print(token + " -- doesn't exist in dictionary")

    search_vec_len = np.linalg.norm(zeros)

    scores = []
    for i, vector in enumerate(indexes):
        scores.append((np.divide(np.matmul(vector, zeros), (doc_vec_len[i] * search_vec_len)), paths[i]))

    scores.sort(reverse=True)

    print("First 10 search results:")
    for i in range(10):
        print(scores[i][1])

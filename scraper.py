from bs4 import BeautifulSoup
from queue import Queue
from pymystem3 import Mystem
from nltk.tokenize import RegexpTokenizer
import httplib2
import re
import math
import scipy
import numpy as np

SCHEME_HOST = 'http://developer.alexanderklimov.ru'
START_PATH = "/android"
ONLY_START_PATH = True
PATH_TO_DIR = "sites"
# -1 For unlimited
MAX_PAGES = 40


def load_site(domain):
    http = httplib2.Http()
    status, response = http.request(domain)
    return status, response


def get_parser(response):
    return BeautifulSoup(response, "lxml")


def find_links(soup):
    links = []
    for link in soup.findAll('a'):
        try:
            links.append(link["href"])
        except KeyError:
            None
    return links


def is_link_valid(link):
    is_link = not (link.__contains__("javascript:") or link.startswith("#"))
    if ONLY_START_PATH:
        is_the_same_domain = link.startswith(START_PATH)
    else:
        is_the_same_domain = link.startswith("/")
    is_not_file = (not link.__contains__(".")) or link.__contains__(".html") or link.__contains__(".php")
    return is_link and is_the_same_domain and is_not_file


def beautify(link, domain):
    if link.startswith(domain):
        link = link[len(domain):]

    link = strip_query_and_fragment(link)
    link = strip_double_slashes(link)

    if link.endswith("/"):
        link = link[:len(link) - 1]

    return link


def get_text(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(strip=True, separator=" ")


def write_to_file(domain, visited_paths, texts):
    index_path = strip_double_slashes(PATH_TO_DIR + "/index.txt")
    f = open(index_path, "w+")
    for i in range(len(texts)):
        f.write(str(i) + " " + domain + visited_paths[i] + "\n")
        file_path = strip_double_slashes(PATH_TO_DIR + "/" + str(i) + ".txt")
        file = open(file_path, "w+")
        file.write(texts[i])
        file.close()
    f.close()


def write_lemmas(lemmas):
    for i in range(len(lemmas)):
        file_path = strip_double_slashes(PATH_TO_DIR + "/" + str(i) + "lemma.txt")
        file = open(file_path, "w+")
        file.write(lemmas[i].__str__())
        file.close()


def strip_double_slashes(link):
    return re.sub('/+', '/', link)


def strip_query_and_fragment(link):
    try:
        return link[:link.index("?")]
    except ValueError:
        try:
            return link[:link.index("#")]
        except ValueError:
            return link


def tokenize(text):
    tokenizer = RegexpTokenizer(r'\w+')
    return tokenizer.tokenize(text)


def lemmatize(texts):
    m = Mystem()
    lemmas_all = []
    for text in texts:
        tokens = tokenize(text)
        lemmas = [m.lemmatize(token.lower())[0] for token in tokens]
        lemmas_all.append(lemmas)
    return lemmas_all


def get_reversed_map(lemmas, visited_paths):
    inverse_map = {}
    for index, path in enumerate(visited_paths):
        for token in lemmas[index]:
            if token not in inverse_map:
                inverse_map[token] = []
            if path not in inverse_map[token]:
                inverse_map[token].append(path)
    return inverse_map


def write_reversed_indexes(inverse_map, visited_paths):
    index_path = strip_double_slashes(PATH_TO_DIR + "/reversed_index.txt")
    f = open(index_path, "w+")
    for token in inverse_map.keys():
        f.write(token + " ")
        for visited_path in visited_paths:
            if visited_path in inverse_map[token]:
                f.write("1 ")
            else:
                f.write("0 ")
        f.write("\n")
    f.close()


def calculate_tf_idf(visited_paths, lemmas, inverse_map):
    tf = {}
    doc_count = len(lemmas)
    for index, path in enumerate(visited_paths):
        for token in inverse_map.keys():
            if token not in tf:
                tf[token] = []
            temp_tf = float(lemmas[index].count(token)) / float(len(lemmas[index]))
            tf[token].append(temp_tf)
    tf_idf = {}
    idf = {}
    for token in inverse_map.keys():
        df = 0
        for path in visited_paths:
            if path in inverse_map[token]:
                df += 1
        idf_item = math.log2(float(doc_count) / float(df))
        idf[token] = idf_item
        for tf_item in tf[token]:
            if token not in tf_idf:
                tf_idf[token] = []
            tf_idf[token].append(tf_item * idf_item)
    return tf_idf, idf


def write_tf_idf(tf_idf, idf):
    index_path = strip_double_slashes(PATH_TO_DIR + "/tf_idf.txt")
    f = open(index_path, "w+")
    for token in tf_idf.keys():
        f.write(token + " ")
        for arr in tf_idf[token]:
            f.write(str(arr) + " ")
        f.write(str(idf[token]))
        f.write("\n")
    f.close()


def calculate_page_rank(from_to, paths):
    matrix = np.zeros(shape=(len(paths), len(paths)))
    for pfrom in from_to.keys():
        link_count = len(from_to[pfrom])
        try:
            col = paths.index(pfrom)
            for link in from_to[pfrom]:
                matrix[paths.index(link)][col] = 1 / link_count
        except ValueError:
            None

    vec = np.linalg.eig(matrix)

    index_path = strip_double_slashes(PATH_TO_DIR + "/page_rank.txt")
    f = open(index_path, "w+")

    for path, value in zip(paths, vec[0]):
        f.write(path + " %.200f" % abs(value) + "\n")


if __name__ == '__main__':
    # Prepare
    path = START_PATH
    link_queue = Queue()
    visited_paths = []
    texts = []
    from_to = {}

    # Start iteration
    while True:
        # Next one if visited
        if path in visited_paths:
            if link_queue.empty():
                break
            else:
                path = link_queue.get()
                continue

        # Create url
        url = SCHEME_HOST + path
        # Load site
        status, response = load_site(url)
        print(url, status.status)

        if status.status == 200:
            # Add to visited
            visited_paths.append(path)
        else:
            if link_queue.empty():
                break
            else:
                path = link_queue.get()
                continue

        # Prepare parser
        soup = get_parser(response)

        # Add text
        text = get_text(soup)
        texts.append(text)

        # Find all links
        links = find_links(soup)
        # Make thy similar form
        links = [beautify(ll, SCHEME_HOST) for ll in links]

        # Add to queue if valid
        for link in links:
            if is_link_valid(link):
                link_queue.put(link)
                if path not in from_to:
                    from_to[path] = []
                from_to[path].append(link)

        # Stop iteration
        if link_queue.empty() or (0 < MAX_PAGES <= len(visited_paths)):
            break

        path = link_queue.get()

    calculate_page_rank(from_to, visited_paths)
    write_to_file(SCHEME_HOST, visited_paths, texts)
    lemmas = lemmatize(texts)
    write_lemmas(lemmas)

    inverse_map = get_reversed_map(lemmas, visited_paths)
    write_reversed_indexes(inverse_map, visited_paths)

    tf_idf, idf = calculate_tf_idf(visited_paths, lemmas, inverse_map)

    write_tf_idf(tf_idf, idf)

from bs4 import BeautifulSoup
from queue import Queue
import httplib2
import re

SCHEME_HOST = 'https://developer.android.com'
START_PATH = "/guide"
ONLY_START_PATH = True
PATH_TO_DIR = "sites/"
# -1 For unlimited
MAX_PAGES = -1


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
    is_not_file = not (link.__contains__(".") and not link.__contains__(".html"))
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
    return soup.get_text(strip=False, separator="")


def write_to_file(domain, visited_paths, texts):
    index_path = strip_double_slashes(PATH_TO_DIR + "/index.txt")
    f = open(index_path, "w+")
    f.write(domain + "\n")
    for i in range(len(texts)):
        f.write(str(i) + " " + visited_paths[i] + "\n")
        file_path = strip_double_slashes(PATH_TO_DIR + "/" + str(i) + ".txt")
        file = open(file_path, "w+")
        file.write(texts[i])
        file.close()
    f.close()


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


if __name__ == '__main__':
    # Prepare
    path = START_PATH
    link_queue = Queue()
    visited_paths = []
    texts = []

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

        # Stop iteration
        if link_queue.empty() or (0 < MAX_PAGES <= len(visited_paths)):
            break

        path = link_queue.get()

    write_to_file(SCHEME_HOST, visited_paths, texts)

from bs4 import BeautifulSoup
from queue import Queue
import httplib2

DOMAIN = 'https://en.wikipedia.org'


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
            print("heh")
    return links


def is_link_valid(link):
    is_link = not (link.__contains__("javascript:") or link.startswith("#"))
    is_the_same_domain = link.startswith("/")
    is_not_file = not (link.__contains__(".") and not link.__contains__(".html"))
    return is_link and is_the_same_domain and is_not_file


def beautify(link, domain, path_now):
    if link.startswith(domain):
        link = link[len(domain):]
    elif link.startswith("/"):
        link = path_now + link

    if link.endswith("/"):
        link = link[:len(link) - 1]

    return link


def get_text(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(strip=True, separator="\n")


def write_to_file(domain, visited_paths, texts):
    f = open("index.txt", "w+")
    f.write(domain + "\n")
    for path in visited_paths:
        f.write(path + "\n")
    f.close()
    for i in range(len(texts)):
        f = open(str(i) + ".txt", "w+")
        f.write(texts[i])
        f.close()


if __name__ == '__main__':
    # Prepare
    path = ""
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
        url = DOMAIN + path
        # Load site
        status, response = load_site(url)
        print(status)

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
        links = [beautify(ll, DOMAIN, path) for ll in links]

        # Add to queue if valid
        for link in links:
            if is_link_valid(link):
                link_queue.put(link)

        # Stop iteration
        if link_queue.empty():
            break

        path = link_queue.get()

    write_to_file(DOMAIN, visited_paths, texts)

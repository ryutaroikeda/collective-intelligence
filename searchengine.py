from html.parser import HTMLParser
import requests

class Link:
    def __init__(self, href, text):
        self.href = href
        self.text = text

class SearchEngineHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self.last_tag = None
        self.last_data = None

    def get_links(self):
        return self.links

    def handle_starttag(self, tag, attributes):
        self.last_tag = tag
        if 'a' != tag:
            return
        for (key, value) in attributes:
            if 'href' == key:
                self.links.append(value)
                return

    def handle_endtag(self, tag):
        self.last_

    def handle_data(self, data):
        self.last_data = data

class Crawler:

    def __init__(self, dbname):
        self.dbname = dbname

    def __del__(self):
        pass

    def crawl(self, pages, depth):
        for i in range(depth):
            new_pages = set()
            for page in pages:
                try:
                    response = requests.get(page)
                except:
                    print('failed to read ' + page)

                self.add_to_index(page, response.text)
                parser = SearchEngineHTMLParser()
                parser.feed(response.text)
                links = parser.get_links()

    def dbcommit(self):
        pass

    def get_entry_id(self):
        pass

    def add_to_index(self, page, content):
        print('indexing ' + page)
        pass

    def add_link_ref(self, page, url, linktext):
        pass

    def extract_text(self, html):
        pass

if __name__ == '__main__':
    url = 'https://kiwitobes.com'
    crawler = Crawler('')
    crawler.crawl([url], 1)

from html.parser import HTMLParser
import re
import requests
import sqlite3
import urllib

class Link:
    def __init__(self, href, text):
        self.href = href
        self.text = text

class HTMLLinkParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self.last_tag = None
        self.last_href = None
        self.last_data = None

    def get_links(self):
        return self.links

    def handle_starttag(self, tag, attributes):
        self.last_href = None
        self.last_tag = tag
        if 'a' != tag:
            return
        for (key, value) in attributes:
            if 'href' == key:
                self.last_href = value

    def handle_endtag(self, tag):
        if self.last_tag != 'a':
            return
        self.links.append(Link(self.last_href, self.last_data))

    def handle_data(self, data):
        self.last_data = data

class HTMLTextParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text = ''
        self.tags = []

    def get_text(self):
        return self.text

    def get_tag(self):
        if not self.tags:
            return None
        return self.tags[-1]

    def should_ignore(self, tag):
        return tag in ['script']

    def handle_starttag(self, tag, attributes):
        self.tags.append(tag.lower())

    def handle_endtag(self, tag):
        if (tag == self.get_tag()):
            self.tags.pop()
        self.text += '\n'

    def handle_data(self, data):
        if self.should_ignore(self.get_tag()): return
        self.text += data

class Crawler:

    def __init__(self, database, ignored_words=[]):
        self.con = database
        self.ignored_words = ignored_words

    def crawl(self, pages, depth):
        for i in range(depth):
            new_pages = set()
            for page in pages:
                try:
                    response = requests.get(page)
                except:
                    print('failed to read ' + page)
                    continue

                parser = HTMLLinkParser()
                parser.feed(response.text)
                links = parser.get_links()

                for link in links:
                    # the href might be relative to the current page
                    url = urllib.parse.urljoin(page, link.href)
                    url_parts = urllib.parse.urlparse(url)
                    # todo?
                    normalized_url = url
                    if 'http' in url_parts.scheme and \
                            not self.is_indexed(normalized_url):
                        new_pages.add(url)

                    if not self.is_indexed(page):
                        self.add_link_ref(page, normalized_url, link.text)

                self.add_to_index(page, response.text, self.ignored_words)
                self.commit()

            pages = new_pages

    def get_text_only(self, html):
        return html

    def separate_words(self, text):
        pattern = re.compile('[\W_]')
        words = [pattern.sub('', s).lower() for s in text.split()]
        return [s for s in words if s]

    def commit(self):
        self.con.commit()

    def get_entry_id(self, table, column, value):
        # this is an insecure hack
        cursor = self.con.execute(
                'SELECT rowid FROM {} WHERE {} = ?'.format(table, column),
                    (value,))
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        cursor = self.con.execute(
                'INSERT INTO {}({}) VALUES (?)'.format(table, column),
                (value,))
        return cursor.lastrowid


    def add_to_index(self, url, content, ignored_words):
        if self.is_indexed(url):
            return
        print('indexing ' + url)
        parser = HTMLTextParser()
        parser.feed(content)
        text = parser.get_text()
        words = self.separate_words(text)

        url_id = self.get_entry_id('url', 'url', url)

        for i in range(len(words)):
            word = words[i]
            if word in ignored_words:
                continue
            word_id = self.get_entry_id('word', 'word', word)
            self.con.execute('''INSERT INTO word_location(url_id,
                word_id, location) VALUES (?, ?, ?)''', (url_id, word_id, i))

    def add_link_ref(self, page, url, linktext):
        from_id = self.get_entry_id('url', 'url', page)
        to_id = self.get_entry_id('url', 'url', url)
        cursor = self.con.execute(
                'INSERT INTO link(from_id, to_id) VALUES (?,?)',
                (from_id, to_id))
        link_id = cursor.lastrowid
        words = self.separate_words(linktext)
        for word in words:
            word_id = self.get_entry_id('word', 'word', word)
            self.con.execute(
            'INSERT INTO link_words(word_id, link_id) VALUES (?,?)',
            (word_id, link_id))

    def is_indexed(self, url):
        indexed_url = self.con.execute(
                'SELECT rowid FROM url WHERE url = ?', (url,)).fetchone()
        if not indexed_url:
            return False
        indexed_word = self.con.execute(
                'SELECT * FROM word_location WHERE url_id = ?',
                (indexed_url[0],)).fetchone()
        return bool(indexed_word)

    def create_index_tables(self):
        self.con.execute('CREATE TABLE url(url)')
        self.con.execute('CREATE TABLE word(word)')
        self.con.execute('''CREATE TABLE word_location(url_id, word_id, 
            location)''')
        self.con.execute('CREATE TABLE link(from_id integer, to_id integer)')
        self.con.execute('CREATE TABLE link_words(word_id, link_id)')
        self.con.execute('CREATE INDEX word_index ON word(word)')
        self.con.execute('CREATE INDEX url_index ON url(url)')
        self.con.execute('''CREATE INDEX location_index ON
                word_location(word_id)''')
        self.con.execute('CREATE INDEX url_from_index ON link(from_id)')
        self.con.execute('CREATE INDEX url_to_index ON link(to_id)')

if __name__ == '__main__':
    url = 'https://kiwitobes.com'
    dbname = 'searchengine.sqlite3'
    con = sqlite3.connect(dbname)
    crawler = Crawler(con)
    crawler.crawl([url], 2)
    del crawler
    con.close()


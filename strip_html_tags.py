from html.parser import HTMLParser

class HTMLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.convert_charrefs = True
        self.texts = []

    def handle_data(self, data):
        self.texts.append(data)

    def get_data(self):
        return ''.join(self.texts)

def strip_html_tags(html):
    stripper = HTMLStripper()
    stripper.feed(html)
    return stripper.get_data()

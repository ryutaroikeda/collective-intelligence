import feedparser
import json
import re
from strip_html_tags import strip_html_tags

# get title and dictionary of word counts of RSS feed
def get_word_counts(url):
    data = feedparser.parse(url)
    word_count = {}
    for entry in data.entries:
        if 'summary' in entry:
            summary = entry.summary
        elif 'description' in entry:
            summary = entry.description
        else:
            summary = ''

        words = get_words(entry.title + ' ' + summary)
        for word in words:
            word_count.setdefault(word, 0)
            word_count[word] += 1

    return data.feed.title, word_count

def get_words(html):
    string = strip_html_tags(html)
    # split words by non-alpha-numeric characters
    words = re.compile(r'[^A-Z^a-z^0-9]+').split(html)
    return [word.lower() for word in words if word != '']

if __name__ == '__main__':

    RSS_FEED_LIST = 'feedlist.txt'
    WORD_COUNT_OUT = 'wordcount.json'
    BLOG_COUNT_OUT = 'blogcount.json'

    word_counts = {}
    # number of blogs each word appeared in
    blog_counts = {}

    with open(RSS_FEED_LIST, 'r') as feed:
        for url in feed:
            try:
                title, word_count = get_word_counts(url)
                word_counts[title] = word_count
                for word in word_count.keys():
                    blog_counts.setdefault(word, 0)
                    blog_counts[word] += 1
            except:
                print('failed to open ' + url)

    with open(WORD_COUNT_OUT, 'w') as out:
        json.dump(word_counts, out)
    with open(BLOG_COUNT_OUT, 'w') as out:
        json.dump(blog_counts, out)


import json

MAX_FREQUENCY = 0.11
MIN_FREQUENCY = 0.10

def make_word_list(blog_counts):
    word_list = []

    max_blog = max(blog_counts.values())

    for word, blog_count in blog_counts.items():
        frequency = blog_count / max_blog
        if frequency < MIN_FREQUENCY or MAX_FREQUENCY < frequency :
            continue
        word_list.append(word)

    return word_list
        
if __name__ == '__main__':

    BLOG_COUNT_IN = 'blogcount.json'
    WORD_LIST_OUT = 'wordlist.tsv'

    with open(BLOG_COUNT_IN, 'r') as blog_count_in:
        blog_count = json.load(blog_count_in)

    word_list = make_word_list(blog_count)

    with open(WORD_LIST_OUT, 'w') as word_list_out:
        for word in word_list:
            word_list_out.write(word + '\n')


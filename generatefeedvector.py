import csv
import json

def make_blog_data(word_list, word_counts, dst):
    with open(dst, 'w') as out:
        writer = csv.writer(out, delimiter='\t')
        writer.writerow(['blog'] + word_list)
        for blog, word_count in word_counts.items():
            row = [blog]
            for word in word_list:
                if word not in word_count:
                    row.append(0)
                    continue
                row.append(word_count[word])
            writer.writerow(row)

if __name__ == '__main__':

    WORD_LIST = 'wordlist.tsv'
    WORD_COUNTS = 'wordcount.json'
    BLOG_DATA = 'blogdata.tsv'

    with open(WORD_LIST, 'r') as word_list_in:
        word_list = word_list_in.read().splitlines()

    with open(WORD_COUNTS, 'r') as word_counts_in:
        word_counts = json.load(word_counts_in)

    make_blog_data(word_list, word_counts, BLOG_DATA)

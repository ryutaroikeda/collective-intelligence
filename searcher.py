from collections import namedtuple
import sqlite3
import sys

Match = namedtuple('Match', ['url_id', 'locations'])

class Searcher:

    def __init__(self, database):
        self.con = database

    def find_matches(self, search_term):
        fields = ['w0.url_id']
        tables = []
        predicates = []
        word_ids = []
        table_number = 0

        words = search_term.split()
 
        for word in words:
            word_row = self.con.execute(
                    'SELECT rowid FROM word where word = ?',
                    (word,)).fetchone()
            if not word_row:
                continue
            word_id = word_row[0]
            word_ids.append(word_id)
            fields.append('w%d.location' % table_number)
            tables.append('word_location w%d' % table_number)
            predicates.append('w%d.word_id = %d' % (table_number, word_id))
            if table_number > 0:
                predicates.append('w%d.url_id = w%d.url_id'
                        % (table_number - 1, table_number))
            table_number += 1

        if not word_ids:
            return [], []

        sql_query = 'SELECT %s FROM %s WHERE %s' % (
                ', '.join(fields),
                ', '.join(tables),
                'and '.join(predicates))

        cursor = self.con.execute(sql_query)
        matches = [Match(row[0], row[1:]) for row in cursor]
        return matches, word_ids

    def get_scored_list(self, matches, word_ids):
        total_scores = dict([(match.url_id, 0) for match in matches])
        weights = [(1.0, self.frequency_score(matches))]

        for (weight, scores) in weights:
            for url_id in total_scores:
                total_scores[url_id] += weight * scores[url_id]

        return total_scores

    def get_url_name(self, url_id):
        url = self.con.execute(
                'SELECT url FROM url where rowid = ?', (url_id,)).fetchone()
        return url[0]

    def query(self, search_term):
        matches, word_ids = self.find_matches(search_term)
        scores = self.get_scored_list(matches, word_ids)
        return sorted([(score, self.get_url_name(url_id))
            for (url_id, score) in scores.items()],
                reverse=True)

    def normalize_scores(self, scores, small_is_better=False):
        epsilon = 0.000001
        if not scores:
            return scores
        if small_is_better:
            min_score = min(scores.values())
            return dict([(url_id, min_score / max(epsilon, score))
                for (url_id, score) in scores.items()])
        max_score = max(scores.values())
        if 0 == max_score:
            max_score = epsilon
        return dict([(url_id, score / max_score)
            for (url_id, score) in scores.items()])

    def frequency_score(self, matches):
        counts = dict([(match.url_id, 0) for match in matches])
        for match in matches:
            counts[match.url_id] += 1
        return self.normalize_scores(counts, False)

if __name__ == '__main__':
    con = sqlite3.connect('searchengine.sqlite3')
    searcher = Searcher(con)
    query = sys.argv[1]
    results = searcher.query(query)
    for (score, url) in results:
        print('%s\t%s' % (score, url))

    del searcher
    con.close()


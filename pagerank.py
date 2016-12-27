import sqlite3

class PageRank:

    def __init__(self, con):
        self.con = con

    def create_page_rank(self, iterations=20):
        self.con.execute('DROP TABLE IF EXISTS page_rank')
        self.con.execute('CREATE TABLE page_rank(url_id, score)')
        self.con.execute('CREATE TEMPORARY TABLE temp_rank(url_id, score)')

        page_count = self.con.execute(
                'SELECT COUNT(*) FROM url').fetchone()[0]

        self.con.execute(
                'INSERT INTO page_rank SELECT rowid, ? FROM url',
                (1.0 / page_count,))

        damping_factor = 0.85

        for i in range(iterations):
            urls = self.con.execute('SELECT rowid FROM url').fetchall()
            self.con.execute('DELETE FROM temp_rank')
            for url in urls:
                url = url[0]
                inbound_links = set([link[0] for link in self.con.execute(
                        'SELECT DISTINCT from_id FROM link WHERE to_id = ?',
                        (url,)).fetchall()])
                inbound_links.add(url)
                score = (1.0 - damping_factor) / page_count

                for inbound_link in inbound_links:
                    # count outbound links and link to itself
                    total_outbound_links = self.con.execute(
                            '''SELECT COUNT(DISTINCT to_id)
                            FROM link WHERE from_id = ?
                            AND from_id <> to_id''',
                            (inbound_link,)).fetchone()[0] + 1
                    page_rank = self.con.execute(
                            'SELECT score FROM page_rank WHERE url_id = ?',
                            (inbound_link,)).fetchone()[0]
                    score += damping_factor * page_rank / total_outbound_links 

                self.con.execute('INSERT INTO temp_rank(url_id, score) ' +
                    'VALUES (?,?)', (url, score))
                self.con.execute(
                        'UPDATE page_rank SET score = ? WHERE url_id = ?',
                        (score, url))
            self.con.execute('DELETE FROM page_rank')
            self.con.execute('INSERT INTO page_rank SELECT url_id, score ' +
                    'FROM temp_rank')
        self.con.commit()

if __name__ == '__main__':
    con = sqlite3.connect('searchengine.sqlite3')
    pr = PageRank(con)
    pr.create_page_rank(16)
    con.close()


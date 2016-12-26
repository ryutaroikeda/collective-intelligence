import sqlite3

class PageRank:

    def __init__(self, con):
        self.con = con

    def create_page_rank(self, iterations=20):
        self.con.execute('DROP TABLE IF EXISTS page_rank')
        self.con.execute('CREATE TABLE page_rank(url_id, score)')
        self.con.execute('CREATE TEMPORARY TABLE temp_rank(url_id, score)')
        self.con.execute(
                'INSERT INTO page_rank SELECT rowid, 1.0 FROM url')

        damping_factor = 0.85
        outbound_links = dict([row for row in self.con.execute(
                'SELECT from_id, COUNT(*) FROM link GROUP BY from_id'
                ).fetchall()])

        for i in range(iterations):
            urls = self.con.execute('SELECT rowid FROM url').fetchall()
            self.con.execute('DELETE FROM temp_rank')
            for url in urls:
                url = url[0]
                inbound_links = self.con.execute(
                        'SELECT from_id FROM link WHERE to_id = ?',
                        (url,)).fetchall()
                score = 0.0
                for inbound_link in inbound_links:
                    inbound_link = inbound_link[0]
                    total_outbound_links = self.con.execute(
                            'SELECT COUNT(*) FROM link WHERE from_id = ?',
                            (inbound_link,)).fetchone()[0]
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
    pr.create_page_rank()
    con.close()


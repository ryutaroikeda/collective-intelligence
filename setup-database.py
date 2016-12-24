import os
import searchengine

database_path = 'searchengine.sqlite3'
os.remove(database_path)
con = sqlite3.connect(dbname)
crawler = searchengine.Crawler(con)
crawler.create_index_tables()
del crawler
con.close()


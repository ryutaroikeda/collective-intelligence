import math
import sqlite3
import sys

class NeuralNetwork:
    def __init__(self, con):
        self.con = con
        self.word_ids = []
        self.url_ids = []
        self.hidden_ids = set()
        # activation values
        self.a_in = []
        self.a_hidden = []
        self.a_out = []
        # weights
        self.w_in = []
        self.w_out = []

    def make_tables(self):
        self.con.execute('CREATE TABLE hidden(create_key)')
        self.con.execute(
                'CREATE TABLE word_hidden(from_id, to_id, strength)')
        self.con.execute(
                'CREATE TABLE hidden_url(from_id, to_id, strength)')
        self.con.execute(
                'CREATE INDEX hidden_index ON hidden(create_key)')
        self.con.execute(
                '''CREATE INDEX word_hidden_index ON word_hidden(from_id,
                to_id)''')
        self.con.execute(
                '''CREATE INDEX hidden_url_index ON hidden_url(from_id,
                to_id)''')
        self.con.commit()

    def get_table(self, layer):
        if 0 == layer:
            return 'word_hidden'
        return 'hidden_url'

    def get_connection(self, from_id, to_id, layer):
        return self.con.execute(
                '''SELECT strength FROM %s WHERE from_id = ? AND to_id = ?'''
                % self.get_table(layer), (from_id, to_id)).fetchone()

    def get_strength(self, from_id, to_id, layer):
        row = self.get_connection(from_id, to_id, layer)

        if row:
            return row[0]

        if 0 == layer:
            return -0.2
        else:
            return 0.0

    def set_strength(self, from_id, to_id, layer, strength):
        self.con.execute(
                '''INSERT OR REPLACE INTO %s (from_id, to_id, strength)
                VALUES (?,?,?)''' % self.get_table(layer),
                (from_id, to_id, strength))

    def generate_hidden_node(self, word_ids, url_ids):
        if 3 < len(word_ids):
            return
        key = '_'.join(sorted([str(word_id) for word_id in word_ids]))
        row = self.con.execute(
                '''SELECT create_key FROM hidden WHERE create_key = ?''',
                (key,)).fetchone()
        if row:
            return
        cur = self.con.execute('INSERT INTO hidden (create_key) VALUES (?)',
                (key,))
        hidden_id = cur.lastrowid
        for word_id in word_ids:
            self.set_strength(word_id, hidden_id, 0, 1.0 / len(word_ids))
        for url_id in url_ids:
            self.set_strength(hidden_id, url_id, 1, 0.1)
        self.con.commit()

    def get_hidden_ids(self, word_ids, url_ids):
        hidden_ids = set()
        for word_id in word_ids:
            rows = self.con.execute(
                    'SELECT to_id FROM word_hidden WHERE from_id = ?',
                    (word_id,))
            for row in rows:
                hidden_ids.add(row[0])

        for url_id in url_ids:
            rows = self.con.execute(
                    'SELECT from_id FROM hidden_url WHERE to_id = ?',
                    (url_id,))
            for row in rows:
                hidden_ids.add(row[0])

        return hidden_ids 

    def make_network(self, word_ids, url_ids):
        self.word_ids = word_ids
        self.hidden_ids = self.get_hidden_ids(word_ids, url_ids)
        self.url_ids = url_ids

        self.a_in = [1.0] * len(word_ids)
        self.a_hidden = [1.0] * len(self.hidden_ids)
        self.a_out = [1.0] * len(url_ids)

        self.w_in = [[self.get_strength(word_id, hidden_id, 0)
            for word_id in word_ids] for hidden_id in self.hidden_ids]
        self.w_out = [[self.get_strength(hidden_id, url_id, 1)
            for hidden_id in self.hidden_ids] for url_id in url_ids] 

    def feed_forward(self):
        for i in range(len(self.word_ids)):
            self.a_in[i] = 1.0

        for i in range(len(self.hidden_ids)):
            activation = 0.0
            for j in range(len(self.word_ids)):
                activation += self.a_in[j] * self.w_in[i][j]
            self.a_hidden[i] = math.tanh(activation)

        for i in range(len(self.url_ids)):
            activation = 0.0
            for j in range(len(self.hidden_ids)):
                activation += self.a_hidden[j] * self.w_out[i][j]
            self.a_out[i] = math.tanh(activation)
        return self.a_out[:]

    def get_result(self, word_ids, url_ids):
        self.make_network(word_ids, url_ids)
        return self.feed_forward()

    def dtanh(self, x):
        return 1.0 - x * x

    def dump(self):
        print('ain ' + str(len(self.a_in)))
        print('ahidden ' + str(len(self.a_hidden)))
        print('aout ' + str(len(self.a_out)))
        print('win ' + str(len(self.w_in)) + ' x ' + str(len(self.w_in[0])))
        print('wout ' + str(len(self.w_out)) + ' x ' + str(len(self.w_out[0])))

    def back_propagation(self, target, learning_rate=0.5):
        # error in last layer
        # delta(l) = grad_a_l(C) .* grad_z_l(a_l)
        # = (a_l - target) .* dtanh(a_l)
        delta_3 = [(self.a_out[i] - target[i]) * self.dtanh(self.a_out[i])
                for i in range(len(self.a_out))]
        # errors for the nodes in the hidden layer
        delta_2 = [sum([self.w_out[i][j] * delta_3[i]
            for i in range(len(delta_3))]) * self.dtanh(self.a_hidden[j])
            for j in range(len(self.a_hidden))]
        # errors for nodes in the first layer; we don't need these
        #delta_1 = [sum([self.w_in[i][j] * delta_2[i]
        #    for i in range(len(delta_2))]) * self.dtanh(self.a_in[j])
        #    for j in range(len(self.a_in))]
        # update weights
        for i in range(len(self.w_out)):
            for j in range(len(self.w_out[i])):
                self.w_out[i][j] -= learning_rate * delta_3[i] * \
                    self.a_hidden[j]
        for i in range(len(self.w_in)):
            for j in range(len(self.w_in[i])):
                self.w_in[i][j] -= learning_rate * delta_2[i] * \
                    self.a_in[j]

    def train_query(self, word_ids, url_ids, selected_url):
        self.generate_hidden_node(word_ids, url_ids)
        self.make_network(word_ids, url_ids)
        self.feed_forward()
        target = [0.0] * len(url_ids)
        target[url_ids.index(selected_url)] = 1.0
        self.back_propagation(target, learning_rate = 0.5)
        for word_id in word_ids:
            for hidden_id in self.hidden_ids:
                self.set_strength(word_id, hidden_id, 0, self.w_in[i][j])
        for hidden_id in self.hidden_ids:
            for url_id in url_ids:
                self.set_strength(hidden_id, url_id, 1, self.w_out[i][j])
        self.con.commit()

if __name__ == '__main__':
    con = sqlite3.connect('searchengine.sqlite3')
    nn = NeuralNetwork(con)
    if len(sys.argv) < 2:
        print('usage: %s <command>' % sys.argv[0])
        exit()
    if 'build' == sys.argv[1]:
        nn.make_tables()
        exit()


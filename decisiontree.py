from collections import namedtuple
import math
import sys

headers = [
        'referrer', 'location', 'has_read_faq', 'pages_viewed', 'service']

my_data=[['slashdot','USA','yes',18,'None'],
        ['google','France','yes',23,'Premium'],
        ['digg','USA','yes',24,'Basic'],
        ['kiwitobes','France','yes',23,'Basic'],
        ['google','UK','no',21,'Premium'],
        ['(direct)','New Zealand','no',12,'None'],
        ['(direct)','UK','no',21,'Basic'],
        ['google','USA','no',24,'Premium'],
        ['slashdot','France','yes',19,'None'],
        ['digg','USA','no',18,'None'],
        ['google','UK','no',18,'None'],
        ['kiwitobes','UK','no',19,'None'],
        ['digg','New Zealand','yes',12,'Basic'],
        ['slashdot','UK','no',21,'None'],
        ['google','UK','yes',18,'Basic'],
        ['kiwitobes','France','yes',19,'Basic']]

SplitRows = namedtuple('SplitRows', ['attribute_id', 'value', 'matches',
    'mismatches'])
Row = namedtuple('Row', ['attributes', 'result'])

class Node:
    def __init__(self, attribute_id=-1, value=None, results=None,
            match_node=None, mismatch_node=None):
        self.attribute_id = attribute_id
        self.value = value
        self.results = results
        self.match_node = match_node
        self.mismatch_node = mismatch_node

def get_rows(rows):
    result = []
    for row in rows:
        result.append(Row(row[:-1], row[-1]))
    return result

def split_rows_on_attribute(rows, attribute_id, value):
    results = SplitRows(attribute_id, value, [], [])
    for row in rows:
        if isinstance(value, int):
            if value >= row.attributes[attribute_id]:
                results.matches.append(row)
                continue
        if value == row.attributes[attribute_id]:
            results.matches.append(row)
            continue
        results.mismatches.append(row)
    return results

def count_results(rows):
    results = {}
    for row in rows:
        results.setdefault(row.result, 0)
        results[row.result] += 1
    return results

def gini_impurity(rows):
    results = count_results(rows)
    gini = 1.0
    for _, result in results.items():
        gini -= pow(result / len(rows), 2)
    return gini

def entropy(rows):
    results = count_results(rows)
    return -1.0 * sum([(result / len(rows)) * math.log(result / len(rows))
        for _, result in results.items()])

def build_tree(rows, score=entropy):
    if 0 == len(rows):
        return Node()
    attribute_num = len(rows[0].attributes)
    current_score = score(rows)

    best_gain = 0.0
    best_split = None

    for attribute_id in range(attribute_num):
        values = set()
        for row in rows:
            values.add(row.attributes[attribute_id])
        for value in values:
            split = split_rows_on_attribute(rows, attribute_id, value)
            p = len(split.matches) / len(rows)
            information_gain = current_score - (p * score(split.matches) +
                    (1 - p) * score(split.mismatches))
            if 0 == len(split.matches) or 0 == len(split.mismatches):
                continue
            if best_gain <= information_gain:
                best_gain = information_gain
                best_split = split

    if 0.0 < best_gain:
        match_node = build_tree(best_split.matches, score)
        mismatch_node = build_tree(best_split.mismatches, score)
        return Node(best_split.attribute_id, best_split.value, None,
                match_node, mismatch_node)
    return Node(None, None, rows, None, None)

def print_tree(node, indent=''):
    if node.results:
        print(count_results(node.results))
        return
    assert 0 <= node.attribute_id
    print(headers[node.attribute_id] + ': ' + str(node.value) + '?')
    sys.stdout.write(indent + 'true-> ')
    print_tree(node.match_node, indent + '    ')
    sys.stdout.write(indent + 'false-> ')
    print_tree(node.mismatch_node, indent + '    ')

def classify(tree, observation):
    if tree.results:
        return count_results(tree.results)
    if isinstance(tree.value, int):
        if observation[tree.attribute_id] >= tree.value:
            return classify(tree.match_node, observation)
    if observation[tree.attribute_id] == tree.value:
        return classify(tree.match_node, observation)
    return classify(tree.mismatch_node, observation)

def prune(tree, max_gain, score=entropy):
    if not tree.match_node or not tree.mismatch_node:
        return
    if tree.match_node.results and tree.mismatch_node.results:
        rows = tree.match_node.results + tree.mismatch_node.results
        p = len(tree.match_node.results) / len(rows)
        information_gain = score(rows) - \
                (p * score(tree.match_node.results) + \
                ((1 - p) * score(tree.mismatch_node.results)))
        if information_gain < max_gain:
            tree.match_node = None
            tree.mismatch_node = None
            tree.results = rows
        return

    if tree.match_node:
        prune(tree.match_node, max_gain, score)
    if tree.mismatch_node:
        prune(tree.mismatch_node, max_gain, score)

if __name__ == '__main__':
    rows = get_rows(my_data)
    tree = build_tree(rows, entropy)
    print_tree(tree)
    print(classify(tree, ['Google', 'USA', 'yes', 30]))
    prune(tree, 1.5)
    print_tree(tree)


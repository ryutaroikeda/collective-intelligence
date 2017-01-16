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
        if value == row.attributes[attribute_id]:
            results.matches.append(row)
        else:
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
    return Node(None, None, count_results(rows), None, None)

def print_tree(node, indent=''):
    if node.results:
        print(node.results)
        return
    assert 0 <= node.attribute_id
    print(headers[node.attribute_id] + ': ' + str(node.value) + '?')
    sys.stdout.write(indent + 'true-> ')
    print_tree(node.match_node, indent + '    ')
    sys.stdout.write(indent + 'false-> ')
    print_tree(node.mismatch_node, indent + '    ')

if __name__ == '__main__':
    rows = get_rows(my_data)
    tree = build_tree(rows)
    print_tree(tree)


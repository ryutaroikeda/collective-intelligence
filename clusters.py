from math import sqrt
from PIL import Image, ImageDraw, ImageFont

CLUSTER_PIXEL_HEIGHT = 20
DENDOGRAM_WIDTH = 1200

def read_file(filename):
    with open(filename, 'r') as fin:
        lines = fin.readlines()
        col_names = lines[0].strip().split('\t')[1:]
        row_names = []
        data = []
        for line in lines[1:]:
            p = line.strip().split('\t')
            row_names.append(p[0])
            data.append([float(x) for x in p[1:]])
    return col_names, row_names, data

def pearson(v1, v2):
    sum1 = sum(v1)
    sum2 = sum(v2)
    sumSquared1 = sum([pow(v, 2) for v in v1])
    sumSquared2 = sum([pow(v, 2) for v in v2])
    sumProduct = sum([v1[i] * v2[i] for i in range(len(v1))])
    numerator = sumProduct - (sum1 * sum2 / len(v1))
    denominator = sqrt((sumSquared1 - pow(sum1, 2) / len(v1)) *
            (sumSquared2 - pow(sum2, 2) / len(v1)))
    if 0 == denominator:
        return 0.0

    return 1.0 - (numerator / denominator)

class bicluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.vec = vec
        self.left = left
        self.right = right
        self.distance = distance
        self.id = id

def hcluster(rows, distance=pearson):
    distances = {}
    current_cluster_id = -1
    clusters = [bicluster(rows[i], id=i) for i in range(len(rows))]

    while len(clusters) > 1:
        closest_pair = (0, 1)
        closest_distance = distance(clusters[0].vec, clusters[1].vec)

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                pair = (clusters[i].id, clusters[j].id)
                if pair not in distances:
                    distances[pair] = distance(clusters[i].vec,
                            clusters[j].vec)
                if distances[pair] < closest_distance:
                    closest_distance = distances[pair]
                    closest_pair = (i, j)
        merged_vec = [(clusters[closest_pair[0]].vec[k] + 
            clusters[closest_pair[1]].vec[k]) / 2.0
            for k in range(len(clusters[0].vec))]

        new_cluster = bicluster(merged_vec, left=clusters[closest_pair[0]],
                right=clusters[closest_pair[1]], distance=closest_distance,
                id=current_cluster_id)

        current_cluster_id -= 1
        # order matters
        del clusters[closest_pair[1]]
        del clusters[closest_pair[0]]
        clusters.append(new_cluster)
    return clusters[0]

def print_cluster(cluster, labels=None, n=0):
    for i in range(n):
        print(' ', end='')
    if cluster.id < 0:
        print('-')
    else:
        if labels == None:
            print(cluster.id)
        else:
            print(labels[cluster.id])
    if cluster.left != None:
        print_cluster(cluster.left, labels=labels, n=n+1)
    if cluster.right != None:
        print_cluster(cluster.right, labels=labels, n=n+1)

def get_height(cluster):
    if cluster.left == None and cluster.right == None:
        return 1
    return get_height(cluster.left) + get_height(cluster.right)

def get_depth(cluster):
    if cluster.left == None and cluster.right == None:
        return 0.0
    return max(get_depth(cluster.left),
            get_depth(cluster.right)) + cluster.distance

def draw_node(draw, cluster, x, y, scaling, labels, font):
    if cluster.id < 0:
        h1 = get_height(cluster.left) * CLUSTER_PIXEL_HEIGHT
        h2 = get_height(cluster.right) * CLUSTER_PIXEL_HEIGHT
        top = y - (h1 + h2) / 2
        bottom = y + (h1 + h2) / 2
        line_length = cluster.distance * scaling

        draw.line([x, top + h1 / 2, x, bottom - h2 / 2], fill=(255, 0, 0))
        draw.line([x, top + h1 / 2, x + line_length, top + h1 / 2],
                fill=(255, 0, 0))
        draw.line([x, bottom - h2 / 2, x + line_length, bottom - h2 / 2],
                fill=(255, 0, 0))
        draw_node(draw, cluster.left, x + line_length, top + h1 / 2,
                scaling, labels, font)
        draw_node(draw, cluster.right, x + line_length, bottom - h2 / 2,
                scaling, labels, font)
    else:
        draw.text((x + 5, y - 7), labels[cluster.id], fill=(0, 0, 0),
                font=font)

def draw_dendrogram(cluster, labels, font, jpeg='clusters.jpg'):
    height = get_height(cluster) * CLUSTER_PIXEL_HEIGHT
    width = DENDOGRAM_WIDTH
    depth = get_depth(cluster)
    scaling = float (width - 150) / depth
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.line([0, height / 2, 10, height / 2], (255, 0, 0))
    draw_node(draw, cluster, 10, height / 2, scaling, labels, font)
    image.save(jpeg, 'JPEG')

if __name__ == '__main__':
    colnames, rownames, rows = read_file('blogdata.tsv')
    cluster = hcluster(rows, pearson)
    unicode_font = ImageFont.truetype('DejaVuSans.ttf', 12)
    #print_cluster(cluster, labels=rownames)
    draw_dendrogram(cluster, rownames, unicode_font)


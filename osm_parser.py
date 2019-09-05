import xml.etree.ElementTree as et
import numpy as np

class Node:
    def __init__(self, id, lat, lon, height=0):
        self.id = id
        self.coords = np.array([lat, lon, height])

class Way:
    def __init__(self, id):
        self.id = id
        self.nodes_ids = []
        self.tags = {}
    
    def add_node(self, node):
        self.nodes_ids.append(node)
    
    def add_tag(self, key, value):
        self.tags[key] = value
    
    def is_closed(self):
        return self.nodes_ids[0] == self.nodes_ids[-1]


def load_data(path='map.osm'):
    tree = et.ElementTree(file=path)
    root = tree.getroot()
    children = list(root)
    nodes = {}
    ways = {}
    for ch in children:
        if ch.tag == 'node':
            id = int(ch.attrib['id'])
            nodes[id] = Node(id, float(ch.attrib['lat']), float(ch.attrib['lon']))
        elif ch.tag == 'way':
            id = int(ch.attrib['id'])
            ways[id] = Way(id)
            for rf in list(ch):
                if(rf.tag == 'nd'):
                    ways[id].add_node(int(rf.attrib['ref']))
                if(rf.tag == 'tag'):
                    ways[id].add_tag(rf.attrib['k'], rf.attrib['v'])
    return (nodes, ways)


if __name__ == '__main__':
    nodes, ways = load_data()

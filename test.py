import osm_parser
import geodetic
import heightmap
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
import json

nodes, ways = osm_parser.load_data()


def plot_way(id, col=''):
    xy = [ltp.from_geog(nodes[i].coords) for i in ways[id].nodes_ids]
    xs = [i[0] for i in xy]
    ys = [i[1] for i in xy]

    if ways[id].is_closed():
        plt.fill(xs, ys, col)
    else:
        plt.plot(xs, ys, color=col)


def plot_ways(*args):
    for id, col in args:
        plot_way(id, col)


# nodes, ways = osm_parser.load_data(r'C:\Users\jhrynko\Downloads\map (3).osm')
nodes, ways = osm_parser.load_data()

with open('config.json', 'r') as config_file:
    CONFIG = json.loads(config_file.read())
    OUTPUT_PREFIX = f"{CONFIG['map']['path']}/{CONFIG['map']['file_name']}"
heightmap = heightmap.Heightmap(CONFIG)


def get_elev_interp(point):
    lat = point[0] * 3600
    lon = point[1] * 3600
    minlat = int(np.floor(lat))
    maxlat = int(np.ceil(lat))
    minlon = int(np.floor(lon))
    maxlon = int(np.ceil(lon))
    # print(minlat, maxlat, minlon, maxlon)
    f00 = heightmap.get_elevation((minlat, minlon), 'sec')
    f01 = heightmap.get_elevation((minlat, maxlon), 'sec')
    f10 = heightmap.get_elevation((maxlat, minlon), 'sec')
    f11 = heightmap.get_elevation((maxlat, maxlon), 'sec')

    f0y = f00 + (f01 - f00) * (lon - minlon)
    f1y = f10 + (f11 - f10) * (lon - minlon)

    fxy = f0y + (f1y - f01) * (lat - minlat)
    return fxy

for k,v in nodes.items():
    v.coords = np.array([v.coords[0], v.coords[1], get_elev_interp((v.coords[0], v.coords[1]))])

ltp = geodetic.LTP([49.628117, 18.915636, 0])

for k, v in ways.items():
    if 'highway' in v.tags:
        plot_way(k, 'darkgray')
    elif 'landuse' in v.tags:
        if v.tags['landuse'] == 'forest':
            plot_way(k, 'darkgreen')
        elif v.tags['landuse'] == 'grass':
            plot_way(k, 'lime')
    elif 'waterway' in v.tags:
        plot_way(k, 'lightblue')
    elif 'building' in v.tags:
        plot_way(k, 'orange')

for i in ways[350362572].nodes_ids:
    print(np.round(ltp.from_geog(nodes[i].coords), 1))


# plot_ways((350362572, 'darkgray'), (237043756, 'darkgray'), (237043757, 'darkgray'), (148306003, 'darkgray'), (300107685, 'darkgray'),
#            (300107684, 'darkgray'), (322480528, 'green'), (327594284, 'lightblue'), (237043759, 'yellow'), (234413315, 'gray'))
plt.axis('equal')
plt.show()

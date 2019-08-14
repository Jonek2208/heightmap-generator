"""Heightmap Generator main module"""
from itertools import product
import json

import numpy as np
import scipy
import scipy.interpolate
import gdal

import geodetic


class Heightmap:
    """Heightmap class"""

    def __init__(self, config):
        self.datasets = {}
        self.elevation_data = {}

        for file in config['files']:
            dataset = gdal.Open(file)
            geo_tf = dataset.GetGeoTransform()
            coords = tuple(map(int, np.round([geo_tf[3], geo_tf[0]])))
            self.datasets[coords] = dataset
            self.elevation_data[coords] = np.array(
                dataset.GetRasterBand(1).ReadAsArray(), dtype="float")

        self.tile_size = (config['map']['tile_size_x'],
                          config['map']['tile_size_y'])
        self.tile_res = config['map']['tile_resolution'] * 1j
        self.min_h = config['map']['minimal_terrain_height']
        # self.max_h = config['map']['maximal_terrain_height']
        self.central_point = np.array([config['map']['center_latitude'],
                                       config['map']['center_longtitude'], 0])
        self.tiles_around = config['map']['tiles_around']

    def get_elevation(self, point, cformat='dec'):
        """Function returns elevation at certain coordinates.

        Mind that for integer coordinates there could be even four possible
        data files from which you can get elevation,
        e.g. (50°N, 18°E) elevation you can get from any of
        theese maps: (50, 18), (50, 17), (51, 17), (51, 18),
        so program needs to check every possibility
        or return error if missing data file."""
        if cformat == 'dms':
            point = (int(np.round(point[0][0] * 3600 + point[0][1] * 60 + point[0][2])),
                     int(np.round(point[1][0] * 3600 + point[1][1] * 60 + point[1][2])))
        elif cformat == 'dec':
            point = (int(np.round(point[0] * 3600)),
                     int(np.round(point[1] * 3600)))
        elif cformat == 'sec':
            point = (int(np.round(point[0])), int(np.round(point[1])))
        else:
            raise Exception("Unknown format")
        candidates = []
        lat = (point[0] // 3600, point[0] % 3600)
        lon = (point[1] // 3600, point[1] % 3600)

        candidates.append([(lat[0] + 1, lat[1])])
        candidates.append([lon])

        if lat[1] == 0:
            candidates[0].append((lat[0], 3600))
        if lon[1] == 0:
            candidates[1].append((lon[0] - 1, 3600))

        for i, j in product(*candidates):
            if (i[0], j[0]) in self.datasets:
                # plt.imshow(elevation_data[(i[0], j[0])], cmap='gray')
                # plt.show()
                return self.elevation_data[(i[0], j[0])][3600 - i[1]][j[1]]
        raise Exception("Missing data file!")

    def elev_from_hmap_area(self):
        """Function get elevation data from points,
        that lie in heightmap area"""
        map_ltp = geodetic.LTP(self.central_point)
        half_tile_y = int(np.ceil((map_ltp.to_geog(np.array(
            [0, self.tile_size[1] / 2, 0])) - self.central_point)[0] * 3600))

        points = []
        values = []

        min_y = -half_tile_y * (2 * self.tiles_around[2] + 1)
        max_y = half_tile_y * (2 * self.tiles_around[0] + 1)

        for delta_y in range(min_y, max_y + 1):
            border_point = map_ltp.to_geog(np.array([self.tile_size[0] / 2, 0, 0]))
            half_tile_x = int(
                np.ceil((border_point - self.central_point)[1] * 3600))
            min_x = -half_tile_x * (2 * self.tiles_around[3] + 1)
            max_x = half_tile_x * (2 * self.tiles_around[1] + 1)
            for delta_x in range(min_x, max_x + 1):
                points.append(map_ltp.from_geog(
                    self.central_point + np.array([delta_y, delta_x, 0]) / 3600)[:2])
                values.append(heightmap.get_elevation(
                    self.central_point * 3600 + np.array([delta_y, delta_x, 0]), cformat='sec'))
        return (points, values)


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        CONFIG = json.loads(config_file.read())
        OUTPUT_PREFIX = f"{CONFIG['map']['path']}/{CONFIG['map']['file_name']}"

    heightmap = Heightmap(CONFIG)

    for tile_nr, (tile_y, tile_x) in enumerate(product(
            range(heightmap.tiles_around[0], -heightmap.tiles_around[2] - 1, -1),
            range(-heightmap.tiles_around[3], heightmap.tiles_around[1] + 1))):
        cx = tile_x * heightmap.tile_size[0]
        cy = tile_y * heightmap.tile_size[1]
        hts = (heightmap.tile_size[0] / 2, heightmap.tile_size[1] / 2)
        grid_x, grid_y = np.mgrid[cx - hts[0]:cx + hts[0]:heightmap.tile_res,
                                  cy - hts[1]:cy + hts[1]:heightmap.tile_res]

        grid_z = scipy.interpolate.griddata(*heightmap.elev_from_hmap_area(),
                                            (grid_x, grid_y), method='cubic')
        flat = grid_z.T.flatten('C')

        flat = (lambda x:
                np.uint16(np.round((x - heightmap.min_h) / 600 * 2**16)))(flat)

        with open(f"{OUTPUT_PREFIX}_{tile_nr}_{tile_x}_{tile_y}.raw", 'w+b') as bin_file:
            bin_file.write(flat.tobytes())

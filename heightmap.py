"""Heightmap Generator main module"""
# import matplotlib
import numpy as np
import matplotlib.pyplot as plt
# import imageio
import scipy
import scipy.interpolate
import gdal
import json
from itertools import product

import geodetic


class Heightmap:
    def __init__(self):
        self.datasets = {}
        self.elevation_data = {}

    def load_data(self, config_file_path='config.json'):
        with open(config_file_path, 'r') as config_file:
            config = json.loads(config_file.read())
            for file in config['files']:
                dataset = gdal.Open(file)
                geo_tf = dataset.GetGeoTransform()
                coords = tuple(map(int, np.round([geo_tf[3], geo_tf[0]])))
                self.datasets[coords] = dataset
                self.elevation_data[coords] = np.array(
                    dataset.GetRasterBand(1).ReadAsArray(), dtype="float")
        self.tile_size_x = config['map']['tile_size_x']
        self.tile_size_y = config['map']['tile_size_y']
        self.tile_res = config['map']['tile_resolution'] * 1j
        self.min_h = config['map']['minimal_terrain_height']
        self.max_h = config['map']['maximal_terrain_height']
        self.central_point = np.array([config['map']['center_latitude'],
                                       config['map']['center_longtitude'], 0])
        self.tiles_around = config['map']['tiles_around']
        self.path = config['map']['path']
        self.file_name = config['map']['file_name']

    def get_elevation(self, point, cformat='dec'):
        """Function returns elevation at certain coordinates.

        Mind that for integer coordinates there could be even four possible data files from which you can get elevation,
        e.g. (50°N, 18°E) elevation you can get from any of theese maps: (50, 18), (50, 17), (51, 17), (51, 18),
        so program needs to check every possibility of return error if missing data file."""
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


# print(get_elevation(CENTRAL_POINT))

#         # imageio.imwrite('map_{}_{}.raw'.format(
#         #     i, j), grid_z.T, format='RAW-FI')
#         # scipy.misc.toimage(grid_z.T, cmin=minh, cmax=maxh).save('map{}{}.png'.format(i, j))
# # print(grid_z.T)
# plt.imshow(grid_z.T, extent=(-TILE_SIZE_X, TILE_SIZE_X, -
#  TILE_SIZE_Y, TILE_SIZE_Y), origin='lower', cmap='gray')
# # plt.plot([it[0] for it in check_points], [it[1] for it in check_points], 'ro')
# plt.show()

# elevation_data = {np.array(dataset[key].GetRasterBand(1).ReadAsArray(), dtype="float") for key in dataset}
# elevation = {}
# for ds in datasets:
#     coords = tuple(map(int, np.round(ds.GetGeoTransform()[0:4:3])))
#     print(coords)
#     print("Projection is {}".format(ds.GetProjection()))
#     print("Driver: {}/{}".format(ds.GetDriver().ShortName,
#                                  ds.GetDriver().LongName))
#     print("Size is {} x {} x {}".format(ds.RasterXSize,
#                                         ds.RasterYSize,
#                                         ds.RasterCount))
#     elevation[coords] = ds.GetGeoTransform()

# print(elevation)
# if geotransform:
#     print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
#     print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))

if __name__ == "__main__":
    heightmap = Heightmap()
    heightmap.load_data()

    map_ltp = geodetic.LTP(heightmap.central_point, units='deg')
    half_tile_y = int(np.ceil((map_ltp.to_geog(np.array(
        [0, heightmap.tile_size_y / 2, 0]), units='deg') - heightmap.central_point)[0] * 3600))
    # np.set_printoptions(suppress=True)
    # print(half_tile_y)
# print(np.round(map_ltp.to_geog(
#     np.array([0, config['map']['tile_size_y'] / 2, 0]), units='deg'), 6))

points = []
values = []

for i in range(-half_tile_y * (2 * heightmap.tiles_around[2] + 1), half_tile_y * (2 * heightmap.tiles_around[0] + 1) + 1):
    half_tile_x = int(np.ceil((map_ltp.to_geog(np.array(
        [heightmap.tile_size_x / 2, 0, 0]), units='deg') - heightmap.central_point)[1] * 3600))
    for j in range(-half_tile_x * (2 * heightmap.tiles_around[3] + 1), half_tile_x * (2 * heightmap.tiles_around[1] + 1) + 1):
        points.append(map_ltp.from_geog(heightmap.central_point +
                                        np.array([i, j, 0]) / 3600, units='deg')[:2])
        values.append(heightmap.get_elevation(
            heightmap.central_point * 3600 + np.array([i, j, 0]), cformat='sec'))

    grids_x = []
    grids_y = []
    grids_z = []

for k, (j, i) in enumerate(product(range(heightmap.tiles_around[0], -heightmap.tiles_around[2] - 1, -1),
                                   range(-heightmap.tiles_around[3], heightmap.tiles_around[1] + 1))):
    cx = i * heightmap.tile_size_x
    cy = j * heightmap.tile_size_y
    grid_x, grid_y = np.mgrid[cx - heightmap.tile_size_x / 2:cx + heightmap.tile_size_x / 2:heightmap.tile_res,
                              cy - heightmap.tile_size_y / 2:cy + heightmap.tile_size_y / 2:heightmap.tile_res]
    print(cx - heightmap.tile_size_x / 2,
          cx + heightmap.tile_size_x / 2,
          cy - heightmap.tile_size_y / 2, cy + heightmap.tile_size_y / 2)
    grids_x.append(grid_x)
    grids_y.append(grid_y)
    grid_z = scipy.interpolate.griddata(
        points, values, (grid_x, grid_y), method='cubic')
    flat = grid_z.T.flatten('C')
    flat = (lambda x: np.uint16(
        np.round((x - heightmap.min_h)/600*2**16)))(flat)
    grids_z.append(grid_z)
    #         # matplotlib.image.imsave(
    #         #     'map{}{}.png'.format(i, j), grid_z.T, cmap='gray')
    with open(f"{heightmap.path}/{heightmap.file_name}_{k}_{i}_{j}.raw", 'w+b') as bin_file:
        bin_file.write(flat.tobytes())

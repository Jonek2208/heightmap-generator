# heightmap-generator
# Heightmap generator for Unity. 
This generator allows you to generate heightmaps of any size you want.
You can precisely select your central point and parameters of your terrain.
It generates also the 16-bit RAW file, so you can just import it to Unity instead of converting it in GIMP or PS.

# How to use
Download elevation data, like SRTM 1 Arc-Second Global. Datermine parameters of your central point.

Open config.json file and set parameters

* `"files"` - add paths to elevation data files
* `"map"` - map settings
  * `"path"` - heightmaps directory path
  * `"file_name"` - name prefix for heightmap files, e.g. `"map"` - `map_0.raw` `map_1.raw` ... etc.
  * `"center_latitude"` - latitude of central point of terrain 
  * `"center_longtitude"` - longtitude of central point of terrain
  * `"minimal_terrain_height"` - minimal height of terrain (temporary)
  * `"maximal_terrain_height"` - maximal height of terrain (temporary)
  * `"tile_size_x"` - size of terrain tile x-axis
  * `"tile_size_y"` - size of terrain tile y-axis (or z-axis in Unity coordinates system)
  * `"heightmap resolution"` - heightmap resolution (parameter in Unity)
  * `"padding"` - padding around central tile in tiles `[top, right, bottom, left]` (from top view)

# TODO
* Check if it works (and maybe fix) for tricky coordinates
* Easier import to Unity

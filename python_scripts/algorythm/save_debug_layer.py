# -*- coding: utf-8 -*-

import os
import numpy as np

# domyślnie zakłada się że layer to gdf, a output to geojson
# parameter is_csv zmienia to założenie na layer to np array, output to csv 
def save_debug_layer(layer, debug_layers_mode_dir, filename, is_csv=False):
    c_dir = os.getcwd()
    os.chdir(debug_layers_mode_dir)
    
    if is_csv:
        np.savetxt(filename, layer, fmt='%i', delimiter=",")
    else:
        layer.to_file(filename, driver="GeoJSON")
    
    os.chdir(c_dir)
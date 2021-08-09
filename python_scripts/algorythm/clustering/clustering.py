# -*- coding: utf-8 -*-

import copy
import pandas as pd
import geopandas as gpd
import numpy as np

from python_scripts.algorythm.clustering.clustering_lib import Clustering
from python_scripts.algorythm.clustering.bricks_to_geodataframe import bricks_to_geodataframe
from python_scripts.algorythm.save_debug_layer import save_debug_layer

def clustering(polygons, route_table, neighborhoods, FLATS_COLNAME, BRICK_SIZE, 
                gmina_id, count, pointset, ADR_COLNAME, debug_layers_mode_dir, DEBUG_LAYERS_MODE):
    clustering = Clustering(polygons, route_table, neighborhoods, FLATS_COLNAME, BRICK_SIZE, pointset, ADR_COLNAME)

    seeds = clustering.get_init_seeds()

    seeds_combinations_so_far = []
    print("Seedy utworzone")
    while True:
        temp_bricks = clustering.create_temp_bricks(seeds)
        new_seeds = clustering.get_center_bricks(temp_bricks)
        if set(new_seeds) in seeds_combinations_so_far:
            bricks = temp_bricks
            break
        else:
            seeds_combinations_so_far.append(set(new_seeds))
            seeds = new_seeds
            print("nowe seedy:")
            print(new_seeds)
    print("Seedy ustanowione!!")
    if DEBUG_LAYERS_MODE:
        route_table_debug = route_table[:,seeds]
        route_table_debug = np.insert(route_table_debug, 0, np.asarray(seeds), axis=0)
        route_table_debug = np.insert(route_table_debug, 0, range(-1,polygons.shape[0]), axis=1)
        route_table_debug = route_table_debug.astype(int)
        save_debug_layer( route_table_debug, debug_layers_mode_dir, f"{gmina_id}_{count}_f2_macierz_odleglosc.csv", True)
        layer_seeds = polygons.loc[seeds]
        save_debug_layer(layer_seeds, debug_layers_mode_dir, f"{gmina_id}_{count}_f3_seedy.json")
        layer = bricks_to_geodataframe(polygons, bricks, gmina_id, count, ADR_COLNAME)
        save_debug_layer(layer, debug_layers_mode_dir, f"{gmina_id}_{count}_f4_podzial_k-medoids.json")
    improved_bricks = clustering.improve_bricks(bricks)
    if DEBUG_LAYERS_MODE:
        layer = bricks_to_geodataframe(polygons, improved_bricks, gmina_id, count, ADR_COLNAME)
        save_debug_layer(layer, debug_layers_mode_dir, f"{gmina_id}_{count}_f5_poprawki_lokalne.json")
    result_bricks = clustering.fix_topology(improved_bricks)
    if DEBUG_LAYERS_MODE:
        layer = bricks_to_geodataframe(polygons, result_bricks, gmina_id, count, ADR_COLNAME)
        save_debug_layer(layer, debug_layers_mode_dir, f"{gmina_id}_{count}_f6_laczenie_multipoligonow.json")
    result_gdf = bricks_to_geodataframe(polygons, result_bricks, gmina_id, count, ADR_COLNAME)
    print("Cegielki gotowe")
    return result_gdf
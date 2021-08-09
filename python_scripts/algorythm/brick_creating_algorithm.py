# -*- coding: utf-8 -*-

import os
import geopandas as gpd
import pandas as pd
from datetime import datetime

from python_scripts.algorythm.routetable.create_route_table import create_route_table
from python_scripts.algorythm.pointsets.create_pointsets import create_pointsets
from python_scripts.algorythm.points_to_polygons.points_to_polygons import points_to_polygons
from python_scripts.algorythm.clustering.clustering import clustering
from python_scripts.algorythm.neighborhoods.create_neighborhoods import create_neighborhoods
from python_scripts.algorythm.save_debug_layer import save_debug_layer

def brick_creating(INPUT_POINTS, INPUT_DIR, PROCESSING_DIR, FLATS_COLNAME, BUILDING_COLNAME, ADR_COLNAME,
        STREET_COLNAME, HOUSE_NUMBER_COLNAME, BRICK_SIZE, input_region_polygons, gmina_id, DEBUG_LAYERS_MODE):
    start_time = datetime.now()
    starting_dir = os.getcwd()

    debug_layers_mode_dir_base = INPUT_DIR + '/../debug_layers_mode/'
    debug_layers_mode_dir = INPUT_DIR + f'/../debug_layers_mode/{gmina_id[:-3]}'
    if DEBUG_LAYERS_MODE:
        if not os.path.exists(debug_layers_mode_dir_base):
            os.makedirs(debug_layers_mode_dir)
        if not os.path.exists(debug_layers_mode_dir):
            os.makedirs(debug_layers_mode_dir)

    print("Tworzenie pointsetow")
    regions, pointsets = create_pointsets(INPUT_POINTS, input_region_polygons, INPUT_DIR, PROCESSING_DIR)
    os.chdir(starting_dir)

    all_bricks = []
    count = 0
    for region, pointset in list(zip(regions, pointsets)):
        count +=1
        print("Pointset: " + str(count) + "/" + str(len(pointsets)))
        voronoi_polygons, pointset = points_to_polygons(pointset, region, FLATS_COLNAME, BUILDING_COLNAME)
        print("Voronoi gotowe")
        if DEBUG_LAYERS_MODE:
            save_debug_layer(voronoi_polygons, debug_layers_mode_dir, f"{gmina_id}_{count}_f1_voronoie_polaczone.json")
        route_table = create_route_table(pointset)
        neighborhoods = create_neighborhoods(voronoi_polygons)
        bricks = clustering(voronoi_polygons, route_table, neighborhoods, FLATS_COLNAME, BRICK_SIZE,
            gmina_id, count, pointset, ADR_COLNAME, debug_layers_mode_dir, DEBUG_LAYERS_MODE)
        all_bricks.append(bricks)

    all_bricks_one_gdf = gpd.GeoDataFrame(pd.concat(all_bricks, ignore_index=True))

    end_time = datetime.now()
    delta_time = (end_time - start_time)
    print("Główny algorytm wykonany po: " + str(delta_time))
    return all_bricks_one_gdf

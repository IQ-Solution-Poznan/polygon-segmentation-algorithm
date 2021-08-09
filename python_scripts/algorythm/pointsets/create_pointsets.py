# -*- coding: utf-8 -*-

from python_scripts.algorythm.pointsets.pointsets_lib import Pointsets

def create_pointsets(INPUT_POINTS, INPUT_REGION_POLYGONS, INPUT_DIR, PROCESSING_DIR):
    
    #pointset = zbior punktow w jednym regionie utworzonym przez linie tnace
    pointsets = Pointsets(INPUT_POINTS, INPUT_REGION_POLYGONS, INPUT_DIR, PROCESSING_DIR)

    #Wczytanie punktow i regionow z plikow na ktore wskazuja stale INPUT_...
    pointsets.read_points()

    pointsets.read_region_polygons()
    #Stworzenie listy ktora dla kazdego regionu zawiera punkty sie w nim znajdujace (lista geodataframow)
    result_pointsets = pointsets.create_pointsets()

    #Stworzenie listy w ktorej kazdy z elementow to kolejny region (lista geodataframow)
    regions = pointsets.get_regions()
    return regions, result_pointsets
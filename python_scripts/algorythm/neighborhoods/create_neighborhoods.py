# -*- coding: utf-8 -*-

import numpy as np

from python_scripts.region_maker.bricks import Bricks

def create_neighborhoods(voronoi_polygons):
    #Pobranie topologii wykorzystując poprzedni algorytm
    bricks = Bricks(voronoi_polygons, [""], 0) #dummy values, nie mają znaczenia
    neighborhoods = bricks.get_neighborhoods()
    neighborhoods = [n[1] for n in neighborhoods]
    neighborhoods = np.asarray(neighborhoods)
    neighborhoods = neighborhoods - 1

    return neighborhoods
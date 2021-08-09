# -*- coding: utf-8 -*-

import geopandas as gpd

def validate_by_area(gdf1, gdf2):
    threshold = 100

    area1 = gdf1.to_crs("EPSG:2180").geometry.unary_union.area
    area2 = gdf2.to_crs("EPSG:2180").geometry.unary_union.area
    diffrence = abs(area1 - area2)
    
    if diffrence > threshold:
        raise Exception(f"Coś poszło nie tak! Plik wynikowy run2.py ma znacząco inną powierzchnię od początkowego pliku z gminami. \
Różnica wynosi {diffrence} metrów kwadratowych!")
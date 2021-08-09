# -*- coding: utf-8 -*-

import os
import numpy as np
import geopandas as gpd

class Pointsets():
    def __init__(self, INPUT_POINTS, INPUT_REGION_POLYGONS, INPUT_DIR, PROCESSING_DIR):
        self.__input_points = INPUT_POINTS
        self.__input_region_polygons = INPUT_REGION_POLYGONS
        self.__input_dir = INPUT_DIR
        self.__processing_dir = PROCESSING_DIR
    
    def __change_working_dir(self, dir):
        os.chdir(dir)

    def read_points(self):
        filename = os.path.splitext(self.__input_points)[0]
        self.__change_working_dir(self.__input_dir + '\\' + filename)
        self.__points = gpd.read_file(self.__input_points)

    def read_region_polygons(self):
        self.__change_working_dir(self.__processing_dir)
        self.__regions = gpd.read_file(self.__input_region_polygons)

    def __clean_points(self, pointset):
        # https://github.com/geopandas/geopandas/issues/521
        wkb = pointset['geometry'].apply(lambda geom: geom.wkb)
        pointset = pointset.loc[wkb.drop_duplicates().index]
        pointset.reset_index(inplace = True)
        return pointset

    def create_pointsets(self):
        pointsets = []
        for polygon_geom in self.__regions.geometry:
            subset = self.__points[self.__points.within(polygon_geom)].copy()
        
            #Upewnienie się że nie ma kilku punktów z takimi samymi współrzędnymi - jak są to wyrzucić
            clean_subset = self.__clean_points(subset)
            pointsets.append(clean_subset)
        return pointsets
    
    def get_regions(self):
        regions = [gpd.GeoDataFrame(geometry = gpd.GeoSeries(geom)) for geom in self.__regions.geometry]
        return regions
        
# -*- coding: utf-8 -*-

import pandas as pd
from python_scripts.algorythm.points_to_polygons.points_to_polygons_lib import Points2Polygons

def points_to_polygons(pointset, region, FLATS_COLNAME, BUILDING_COLNAME):
        
        points2polygons = Points2Polygons(pointset, region)
        
        #O poniższym argumencie: jest to hardkodowana wartość na oko
        #Oznacza ona wielkość bufora dookoła regionu, którego wierzchołki są punktami dodanymi do procesu tworzenia voronoi
        #Powodem jest wyeliminowanie dziur
        points2polygons.create_voronois(0.5)
        points2polygons.copy_attributes_by_location(FLATS_COLNAME, BUILDING_COLNAME)

        result_polygons, result_pointset = points2polygons.get_result_polygons()

        #Zamiana typu kolumny flats na double!!
        result_polygons[FLATS_COLNAME] = pd.to_numeric(result_polygons[FLATS_COLNAME])


        if len(result_pointset) != len(result_polygons):
                if len(result_pointset) > len(result_polygons):
                        #Usunięcie punktów dla których nie stworzyły się poligony - rzadki przypadek bardzo bliskich punktów
                        for i, poly in result_polygons.iterrows():
                                points_in_polygon = []
                                for j, point in result_pointset.iterrows():
                                        if poly.geometry.contains(point.geometry):
                                                points_in_polygon.append(j)
                                if len(points_in_polygon) > 1:
                                        points_to_delete = points_in_polygon[1:]
                                        result_pointset = result_pointset.drop(points_to_delete)
        if len(result_pointset) != len(result_polygons):
                raise ValueError('Voronoie nie stworzyly sie poprawnie...!')

        return result_polygons, result_pointset
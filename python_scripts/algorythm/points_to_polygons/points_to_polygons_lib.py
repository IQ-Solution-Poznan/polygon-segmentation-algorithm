# -*- coding: utf-8 -*-

import scipy.spatial as sptl
import numpy as np
import shapely
import geopandas as gpd
import pandas as pd

from python_scripts.algorythm.points_to_polygons.copy_attributes_by_location import copy_attributes_by_location

class Points2Polygons():
    def __init__(self, pointset, region):
        self.__pointset = pointset
        self.__region = region
    
    def create_voronois(self, buffer_size):
        x = self.__pointset.geometry.x.values
        y = self.__pointset.geometry.y.values
        coords = np.vstack((x, y)).T

        buffer = self.__region.geometry.buffer(buffer_size)
        if buffer.type.any() == "MultiPolygon":
            buffer = buffer[0][0]
        buffed_region = gpd.GeoDataFrame(geometry = gpd.GeoSeries(buffer))
        if buffed_region.geometry[0].boundary.geom_type == "MultiLineString":
            boundary = buffed_region.geometry[0].boundary[0]
        else:
            boundary = buffed_region.geometry[0].boundary
        boundary_x = boundary.coords.xy[0]
        boundary_y = boundary.coords.xy[1]
        boundary_coords = np.vstack((boundary_x, boundary_y)).T

        #Powtorzenie dla o połowę większego i o połowę mniejszego buforu, dla pewności:
        buffer = self.__region.geometry.buffer(buffer_size*1.25)
        if buffer.type.any() == "MultiPolygon":
            buffer = buffer[0][0]
        buffed_region = gpd.GeoDataFrame(geometry = gpd.GeoSeries(buffer))
        if buffed_region.geometry[0].boundary.geom_type == "MultiLineString":
            boundary = buffed_region.geometry[0].boundary[0]
        else:
            boundary = buffed_region.geometry[0].boundary
        boundary_x = boundary.coords.xy[0]
        boundary_y = boundary.coords.xy[1]
        boundary_coords2 = np.vstack((boundary_x, boundary_y)).T

        buffer = self.__region.geometry.buffer(buffer_size*0.75)
        if buffer.type.any() == "MultiPolygon":
            buffer = buffer[0][0]
        buffed_region = gpd.GeoDataFrame(geometry = gpd.GeoSeries(buffer))
        if buffed_region.geometry[0].boundary.geom_type == "MultiLineString":
            boundary = buffed_region.geometry[0].boundary[0]
        else:
            boundary = buffed_region.geometry[0].boundary
        boundary_x = boundary.coords.xy[0]
        boundary_y = boundary.coords.xy[1]
        boundary_coords3 = np.vstack((boundary_x, boundary_y)).T
        
        #all_cords dla którego robimy voronoie zawiera współrzędne punktów adresowych oraz współrzędne wierzchołków olbrzymiego buforu
        all_coords = np.vstack((coords, boundary_coords, boundary_coords2, boundary_coords3))
        vor = sptl.Voronoi(all_coords)

        #Przekształcenie voronoi do postaci geodataframe
        lines = [shapely.geometry.LineString(vor.vertices[line]) for line in vor.ridge_vertices if -1 not in line]
        polys = shapely.ops.polygonize(lines)
        self.__voronois = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polys))

        #Usunięcie stworzonych niechcianych "szpiczastych" poligonów
        buffer_15 = self.__region.geometry.buffer(buffer_size*1.5)
        within = self.__voronois.geometry.map(lambda x: x.within(buffer_15.geometry.any()))
        self.__voronois = self.__voronois[within]

        #Przyciecie dużej zasięgowo warstwy voronoi przez region
        self.__voronois = gpd.overlay(self.__voronois, self.__region)
        self.__multipart_to_singleparts()

    def __multipart_to_singleparts(self):
        singlepart_df = gpd.GeoDataFrame(columns=self.__voronois.columns)
        for i, row in self.__voronois.iterrows():
            if row.geometry.geom_type == "Polygon":
                singlepart_df = singlepart_df.append(row,ignore_index=True)
            elif row.geometry.geom_type == "MultiPolygon":
                for geom in row.geometry:
                    new_row = row
                    new_row.geometry = geom
                    singlepart_df = singlepart_df.append(new_row,ignore_index=True)
            else:
                print("Nieznana geometria: " + row.geometry.geom_type)
        self.__voronois = singlepart_df
                

    def copy_attributes_by_location(self, flats, building_id):
        self.__pointset['order'] = [str(i) for i in range(self.__pointset.shape[0])]
        attributes = [building_id, flats, 'order']
        self.__result_polygons = copy_attributes_by_location(self.__pointset, self.__voronois, attributes)
        self.__fix_geometry(building_id, flats)
        self.__order_by_column()

    def get_result_polygons(self):
        return self.__result_polygons, self.__pointset

    def __order_by_column(self):
        self.__result_polygons['order'] = pd.to_numeric(self.__result_polygons['order'])
        self.__result_polygons = self.__result_polygons.sort_values(by=['order'])
        self.__result_polygons = self.__result_polygons.set_index('order')
        self.__pointset['order'] = pd.to_numeric(self.__pointset['order'])
        self.__pointset = self.__pointset.set_index('order')

    def __fix_geometry(self, building_id, flats):
        #Poniższy kod usunie pozostałości po dawnych Multipoligonach. Trzeba załatać te dziury
        i = 0
        self.__result_polygons['dissolve_column'] = self.__result_polygons.index
        while True:
            empty_polygons = self.__result_polygons.index[self.__result_polygons[building_id].isnull()].tolist()
            if len(empty_polygons) == 0:
                break
            empty_polygon = empty_polygons[i]
            geom = self.__result_polygons.at[empty_polygon, 'geometry']
            neighbors = self.__result_polygons[~self.__result_polygons.geometry.disjoint(geom)].index.tolist()
            neighbors.remove(empty_polygon)
            #Sprawdzenie czy przypadkiem dwa poligony nie stykają się ze sobą tylko 1 punktem:
            for neighbor in neighbors:
                union = self.__result_polygons.at[empty_polygon, "geometry"].union(self.__result_polygons.dissolve(by='dissolve_column').at[neighbor, "geometry"])
                if union.geom_type == "MultiPolygon":
                    neighbors.remove(neighbor)
            if self.__result_polygons.loc[neighbors][flats].isnull().all():
                i = i+1
                empty_polygon = empty_polygons[i]
            else:
                i = 0
                neighbors_df = self.__result_polygons.loc[neighbors]
                best_neighbor = pd.to_numeric(neighbors_df[flats]).idxmax()
                self.__result_polygons.at[empty_polygon, 'dissolve_column'] = self.__result_polygons.at[best_neighbor, 'dissolve_column']
                self.__result_polygons.at[empty_polygon, building_id] = self.__result_polygons.at[best_neighbor, building_id]
                self.__result_polygons.at[empty_polygon, flats] = self.__result_polygons.at[best_neighbor, flats]
        self.__result_polygons = self.__result_polygons.dissolve(by='dissolve_column')

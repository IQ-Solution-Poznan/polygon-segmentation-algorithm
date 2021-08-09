# -*- coding: utf-8 -*-

import os
import numpy as np
import geopandas as gpd
import requests
import json

class RouteTable():
    def __init__(self, pointset):
        self.__pointset = pointset
    
    def __change_working_dir(self, dir):
        os.chdir(dir)

    def read_coords(self):
        self.__pointset = self.__pointset.to_crs(epsg=4326)
        self.__x = self.__pointset.geometry.x
        self.__y = self.__pointset.geometry.y

    def create_table(self):
        points = list(zip(self.__x, self.__y))
        self.__route_table = self.__send_osrm_request(points)
        self.__route_table = np.asarray(self.__route_table)
        self.__route_table = self.__route_table.reshape(self.__x.size, self.__y.size)

    def __send_osrm_request(self, points):
        request = "http://localhost:5000/table/v1/driving/"
        for point in points:
            request = request + str(point[0]) + "," + str(point[1])
            if point != points[len(points)-1]:
                request = request + ";"
        #wersja lokalna wymaga aktywnego routingu OSRM!
        response = requests.get(request)
        json_response = json.loads(response.text)
        durations = json_response['durations']
        return durations

    def change_none_to_numbers(self):
            nones_indexes = np.argwhere(np.equal(self.__route_table, None))
            for none_indexes in nones_indexes:
                opposite_dist = self.__route_table[none_indexes[1]][[none_indexes[0]]]
                if opposite_dist[0] is not None:
                    self.__route_table[none_indexes[0]][[none_indexes[1]]] = opposite_dist
                else:
                    closest_point_index1 = np.amin(self.__route_table[none_indexes[0]], \
                        initial=100000, where=~np.equal(self.__route_table[none_indexes[0]], None))
                    closest_point_index2 = np.amin(self.__route_table[none_indexes[1]], \
                        initial=100000, where=~np.equal(self.__route_table[none_indexes[1]], None))
                    dist1 = self.__route_table[closest_point_index1][closest_point_index2]
                    dist2 = self.__route_table[closest_point_index2][closest_point_index1]
                    if np.equal(dist1, None):
                        dist1 = dist2
                    if np.equal(dist2, None):
                        dist2 = dist1
                    self.__route_table[none_indexes[0]][[none_indexes[1]]] = dist1
                    self.__route_table[none_indexes[1]][[none_indexes[0]]] = dist2
                    if np.equal(dist1, None) and np.equal(dist2, None):
                        raise ValueError("Błąd w wyznaczaniu macierzy OSRM - wartość 'None' w macierzy")

    def make_symmetric(self):
        self.__route_table = np.minimum(self.__route_table, self.__route_table.T)

    def return_table(self):
        return self.__route_table
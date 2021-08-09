# -*- coding: utf-8 -*-

import math
import numpy as np
import copy 

class Clustering():
    def __init__(self, polygons, route_table, neighborhoods, FLATS_COLNAME, BRICK_SIZE, pointset, ADR_COLNAME):
        self.__polygons = polygons
        self.__route_table = route_table
        self.__neighborhoods = neighborhoods
        self.__flats_colname = FLATS_COLNAME
        self.__brick_size = BRICK_SIZE
        self.__pointset = pointset
        self.__euclidean_table = self.__create_euclidean_table()
        self._adr_colname = ADR_COLNAME

    def __create_euclidean_table(self):
        self.__pointset = self.__pointset.to_crs("EPSG:2180")
        x = self.__pointset.geometry.x
        y = self.__pointset.geometry.y
        coords = list(zip(x, y))
        euclidean_table = []
        for x1, y1 in coords:
            table_row = []
            for x2, y2 in coords:
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                table_row.append(dist)
            euclidean_table.append(table_row)
            table_row = []
        euclidean_table = np.asarray(euclidean_table)

        return euclidean_table

    def get_init_seeds(self):
        #Określenie ile powinno być seedów:
        flats_in_region = self.__polygons[self.__flats_colname].sum()
        number_of_seeds = int(math.floor(flats_in_region / self.__brick_size))
        if number_of_seeds == 0:
            number_of_seeds = 1

        seeds = []
        avg_points_in_brick = int(len(self.__euclidean_table)/number_of_seeds)
        et = np.apply_along_axis(np.sort, 1, self.__euclidean_table)[:,:avg_points_in_brick]
        sum_dists = np.apply_along_axis(np.sum, 1, et)
        unassigned_polygons = np.apply_along_axis(np.argsort, 0, sum_dists)
        for i in range(number_of_seeds):
            if len(unassigned_polygons) != 0:
                seed = unassigned_polygons[0]
                seeds.append(seed)
                polygons_sorted = np.apply_along_axis(np.argsort, 0, self.__euclidean_table[seed])
                polygons_sorted_flats = self.__polygons.loc[polygons_sorted][self.__flats_colname]
                polygons_sorted_flats_cumsum = np.asarray(np.cumsum(polygons_sorted_flats))
                stop_value = np.argwhere(polygons_sorted_flats_cumsum>self.__brick_size*1.5)
                if len(stop_value > 0):
                    stop_value = stop_value[0][0]
                    if stop_value < avg_points_in_brick:
                        if avg_points_in_brick < len(unassigned_polygons):
                            stop_value = avg_points_in_brick
                        else:
                            stop_value = len(unassigned_polygons)
                    discarded_polygons = polygons_sorted[:stop_value]
                    unassigned_polygons = [poly for poly in unassigned_polygons if poly not in discarded_polygons]
                #Sytuacja w której już w pierwszym seedzie wszystkie poligony są zajęte
                elif len(seeds) == 1:
                    discarded_polygons = unassigned_polygons
                    unassigned_polygons = []

        return seeds

    def __create_polygons_rating(self, seeds):
        ratings = self.__route_table[:,seeds]
        if len(seeds) > 1:
            ratings_sums = np.apply_along_axis(np.sum, 1, ratings)
            ratings = (ratings.T/ratings_sums).T
        else:
            ratings[True] = 0

        return ratings

    def __neighborhoods_update(self, neighborhoods_copy, seed, added_polygon):
        neighborhoods_copy[seed] = np.union1d(neighborhoods_copy[added_polygon], neighborhoods_copy[seed])

        neighborhoods_copy[neighborhoods_copy[added_polygon]] = [ np.where(neighborhood==added_polygon, seed, neighborhood) 
            for neighborhood in neighborhoods_copy[neighborhoods_copy[added_polygon]]]
        neighborhoods_copy[neighborhoods_copy[added_polygon]] = [ np.unique(neighborhood) 
            for neighborhood in neighborhoods_copy[neighborhoods_copy[added_polygon]]]
        
        neighborhoods_copy[seed] = neighborhoods_copy[seed][neighborhoods_copy[seed] != seed]
        neighborhoods_copy[added_polygon] = []

    def create_temp_bricks(self, seeds):
        neighborhoods_copy = copy.deepcopy(self.__neighborhoods)
        available_polygons = np.asarray(self.__polygons['index'])
        
        bricks_array = [[seed] for seed in seeds]
        flats_array = np.array([self.__polygons.at[seed, self.__flats_colname] for seed in seeds])

        available_polygons = np.setdiff1d(available_polygons, seeds)
        
        rating = self.__create_polygons_rating(seeds)
        while True:
            current_min_size = flats_array.min()
            best_rating = 101
            i = 0
            for brick, flats in zip(bricks_array, flats_array):
                #Zgadzamy się na wstępne różnice między cegiełkami w regionie - max 3krotne
                if flats <= current_min_size * 3:
                    neighborhood = neighborhoods_copy[brick[0]]
                    neighbors = np.intersect1d(neighborhood,available_polygons)
                    if neighbors.size > 0:
                        rates = rating[neighbors, i]
                        if np.min(rates) < best_rating:
                            best_polygon = neighbors[np.argmin(rates)]
                            best_rating = np.min(rates)
                            best_polygon_brick = i
                i+=1
                    
            if best_rating == 101:
                break
            else:
                bricks_array[best_polygon_brick].append(best_polygon)
                flats_array[best_polygon_brick] += self.__polygons.at[best_polygon, self.__flats_colname]
                available_polygons = np.delete(available_polygons, np.argwhere(available_polygons == best_polygon))
                self.__neighborhoods_update(neighborhoods_copy, bricks_array[best_polygon_brick][0], best_polygon)
        while available_polygons.size != 0:
            best_rating = 101
            i = 0
            for brick in bricks_array:
                neighborhood = np.asarray(neighborhoods_copy[brick[0]])
                neighbors = np.intersect1d(neighborhood,available_polygons)
                if neighbors.size > 0:
                    rates = rating[neighbors, i]
                    if np.min(rates) < best_rating:
                        best_polygon = neighbors[np.argmin(rates)]
                        best_rating = np.min(rates)
                        best_polygon_brick = i
                i+=1
            bricks_array[best_polygon_brick].append(best_polygon)
            flats_array += self.__polygons.at[best_polygon, self.__flats_colname]
            available_polygons = np.delete(available_polygons, np.argwhere(available_polygons == best_polygon))
            self.__neighborhoods_update(neighborhoods_copy, bricks_array[best_polygon_brick][0], best_polygon)

        return bricks_array

    def get_center_bricks(self, bricks_array):
        new_seeds=[]
        for brick in bricks_array:
            dists = self.__route_table[brick][:,brick]
            dists_sum = np.apply_along_axis(np.sum, 1, dists)
            new_seed = brick[np.argmin(dists_sum)]
            new_seeds.append(new_seed)

        return new_seeds

    def __break_point(self, x):
        x[x < 15] = 15
        x0 = np.array([-1])
        vect = np.concatenate((x0,x,x0))
        change_scale = vect[:-1]/vect[1:]
        change_scale = change_scale[1:-1]
        
        change_diffs = change_scale[:-1] - change_scale[1:]
        perc = np.percentile(change_diffs[change_diffs > 0], 95)
        possible_break_points = np.argwhere(change_diffs > perc)
        break_point = possible_break_points[0][0] + 2

        return break_point

    def __get_strongly_connected_polygons(self, polygons_to_check, all_polygons, checked_polygon=None):
        if checked_polygon == None:
            checked_polygon = polygons_to_check[0]
        dists = self.__euclidean_table[checked_polygon]
        order = np.argsort(dists)
        index_order = np.asarray(all_polygons)[order]
        sorted = dists[order]

        if sorted[1] > 50:
            return [checked_polygon]

        break_point = self.__break_point(sorted)
        connected_polygons = index_order[:break_point]

        #odrzucenie poligonów które nie są już w liście polygons_to_check:
        connected_polygons = list(set(connected_polygons).intersection(polygons_to_check))

        #Sprawdzenie topologii:
        topo_connected_polygons = [connected_polygons[0]]
        for cp in connected_polygons[1:]:
            neighbors = self.__neighborhoods[cp]
            if len(set(neighbors).intersection(topo_connected_polygons)) != 0:
                topo_connected_polygons.append(cp)

        return topo_connected_polygons
    
    def __move_connected_polygons(self, connected_polygons, bricks_array):

        polys_inside_bricks = []
        polys_indexes = []
        for brick in bricks_array:
            con_polys = list(set(brick).intersection(connected_polygons))
            polys_inside_bricks.append(len(con_polys))
            polys_indexes.append(con_polys)
        
        new_brick = bricks_array[np.argsort(polys_inside_bricks)[-1]]
        if np.max(polys_inside_bricks) == len(connected_polygons):
            return bricks_array
        for brick, polys in zip(bricks_array, polys_indexes):
            if len(polys) != 0:
                if brick != new_brick:
                    for poly in polys:
                        brick.remove(poly)
                else:
                    to_add = list(set(connected_polygons).difference(polys))
                    for add in to_add:    
                        brick.append(add)

        return bricks_array

    def improve_bricks(self, bricks_array):
        polygons_to_check = self.__polygons['index'].tolist()
        all_polygons = copy.deepcopy(polygons_to_check)
        while len(polygons_to_check) > 1:
            connected_polygons = self.__get_strongly_connected_polygons(polygons_to_check, all_polygons)
            bricks_array = self.__move_connected_polygons(connected_polygons, bricks_array)
            polygons_to_check = np.setdiff1d(polygons_to_check, connected_polygons)
        
        return bricks_array
    
    def __get_islands(self, brick):
        islands = []
        while len(brick) != 0:
            island = [brick[0]]
            brick = brick[1:]
            while True:
                neighbors = self.__neighborhoods[island]
                neighbors = np.concatenate(neighbors).ravel()
                polygons_to_add = list(set(neighbors).intersection(brick))
                island = island + polygons_to_add
                brick = list(set(brick).difference(polygons_to_add))
                if len(polygons_to_add) == 0:      
                    break
            islands.append(island)
        
        return islands

    def __find_brick_by_polygon(self, polygon, bricks_array):
        for brick_id in range(len(bricks_array)):
            if polygon in bricks_array[brick_id]:
                return brick_id

    def fix_topology(self, bricks_array):
        for brick_id in range(len(bricks_array)):
            islands = np.asarray(self.__get_islands(bricks_array[brick_id]))
            if len(islands) > 1:
                lens = [len(polys) for polys in islands]
                sorted = np.argsort(lens)
                sorted = sorted[:len(sorted)-1].tolist()
                for polygons_to_move in islands[sorted]:
                    neighborhood = self.__neighborhoods[polygons_to_move]
                    neighbors = np.concatenate(neighborhood).ravel()
                    neighbors = list(set(neighbors).difference(polygons_to_move))
                    route_table = self.__route_table[neighbors,:][:,polygons_to_move]
                    sums = np.apply_along_axis(np.sum, 1, route_table)
                    best_neighbor_pos = np.argsort(sums)[0]
                    best_neighbor = neighbors[best_neighbor_pos]
                    new_brick_id = self.__find_brick_by_polygon(best_neighbor, bricks_array)
                    for poly in polygons_to_move:
                        bricks_array[brick_id].remove(poly)
                        bricks_array[new_brick_id].append(poly)

        return bricks_array
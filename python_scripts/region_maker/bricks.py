# -*- coding: utf-8 -*-
import json
import topojson as tjson
import pandas as pd
import geopandas as gpd
import numpy as np
import math
import python_scripts.region_maker.topoparser as topoparser
from shapely.geometry import Polygon, LineString

class Bricks():
    def __init__(self, df, COLNAMES, MINIMUM_POINTS):
        self.__df = df
        self.__colnames = COLNAMES
        self.__minimum_points = MINIMUM_POINTS
        self.__compactness_table = []

    def __create_topojson(self):
        #Stworzenie topojsona zgodnie z biblioteka topojson ( https://github.com/mattijn/topojson )
        dictionary = {0: self.__df}
        topology = tjson.Topology(dictionary, prequantize=False, topology=True)
        topojson = topology.to_json()
        topojson_loaded = json.loads(topojson)
        return(topojson_loaded)


    def __identify_neighborhoods(self, topojson):
        #Wyznaczenie list poczatkowych sasiadow za pomoca kodu topoparser
        topo = topoparser.topoparser(topo=topojson)                                                                                                                                                   
        topo.parse()
        neighborhoods = topo.neighborhoods
        neighborhoods = [np.unique(neighborhood) for neighborhood in neighborhoods]
        neighborhoods = [[index+1, neighborhood+1] for index, neighborhood in zip(range(len(neighborhoods)), neighborhoods)]
        neighborhoods = [[neighborhood[0], np.array(neighborhood[1])] for neighborhood in neighborhoods]
        return(neighborhoods)

    def __recalculate_statistic(self, df1, df2, also_return_points=True):
        #Obliczanie ilosci punktow oraz compactness dla polaczenia dwoch dataframeow (ktore moga zawierac jeden lub wiecej obiektow)
        temp_df = pd.concat([df1, df2])
        area = temp_df.unary_union.area
        perimeter = temp_df.unary_union.length
        compactness = perimeter / (2 * math.sqrt(math.pi * area))
        if also_return_points:
            points = temp_df[self.__colnames[4]].sum()
            return(compactness, points)
        else:
            return compactness

    def __get_compactness_score(self, feature, neighbor):
        f_compactness = feature[self.__colnames[3]].values[0]
        n_compactness = neighbor[self.__colnames[3]].values[0]
        #różnica jest liczona z persepktywy obiektu z gorszym compactness startowym
        if f_compactness > n_compactness:
            old_compactness = f_compactness
        else:
            old_compactness = n_compactness


        compactness = self.__recalculate_statistic(feature, neighbor, False)
        compactness_diffrence = compactness - old_compactness
        compactness_score = (compactness_diffrence * 100) / old_compactness
        return compactness_score


    def get_neighborhoods(self):
        #Zwraca poczatkowych sasiadow
        topojson = self.__create_topojson()
        neighborhoods = self.__identify_neighborhoods(topojson)
        neighborhoods = np.asarray(neighborhoods)
        return neighborhoods

    def create_compactness_table(self, neighborhoods):
        #tworzy tabele zawierajaca wszystkie mozliwe pary sasiadow i roznice miedzy aktualnym compactness sasiada a compactness uzyskanym po zlaczeniu poligonow
        for neighborhood in neighborhoods:
            feature_id = neighborhood[0]    
            feature = self.__df.loc[[feature_id]]
            for neighbor_id in neighborhood[1]:
                neighbor = self.__df.loc[[neighbor_id]]
                compactness_score = self.__get_compactness_score(feature, neighbor)
                self.__compactness_table.append([feature_id, neighbor_id, compactness_score])
        self.__compactness_table = pd.DataFrame(self.__compactness_table, columns=list('fnc')) #feature, neighbor, compactness_score

    def if_too_little_points(self, feature_id):
        #Sprawdza czy dany obiekt ma w sobie mniej punktow niz wyznaczone przez nas minimum (i tym samym klasyfikuje sie do dalszego laczenia)
        features = self.__df.loc[(self.__df[self.__colnames[1]] == feature_id)]
        if features[self.__colnames[4]].values.sum() < self.__minimum_points:
            return True
        else:
            return False

    def if_cutline_is_not_crossed(self, feature_id, neighbor_id):
        #Sprawdzenie czy ktorykolwiek z fragmentow feature i neighbor byli poczatkowo czescia jednej cegielki:
        feature = self.__df.loc[self.__df[self.__colnames[1]] == feature_id]
        neighbor = self.__df.loc[self.__df[self.__colnames[1]] == neighbor_id]
        oldid_feature = neighbor[self.__colnames[6]].values
        oldid_neighbor = feature[self.__colnames[6]].values
        if set(oldid_feature) & set(oldid_neighbor):
            return False #metoda zwraca false gdy zbior nie jest pusty
        else:
            return True

    def get_compactness(self, feature, neighbor):
        #zwraca roznice compactness, zapisana w tabeli, dla konktetnej pary obiekt-sasiad
        row = self.__compactness_table.loc[(self.__compactness_table['f'] == feature) & (self.__compactness_table['n'] == neighbor)]
        compactness = row['c'].values[0]
        return compactness

    def update_dataframe(self, what_to_dissolve):
        #nadpisuje kolumny newcompactness i newpoints obliczonymi wczesniej wartosciami
        feature_id = what_to_dissolve[0]
        neighbor_id = what_to_dissolve[1]

        feature = self.__df.loc[self.__df[self.__colnames[1]] == feature_id]
        neighbor = self.__df.loc[self.__df[self.__colnames[1]] == neighbor_id]
        compactness, points = self.__recalculate_statistic(feature, neighbor, True)

        indexes_to_change = [index for index in pd.concat([feature, neighbor]).index]
        for index_to_change in indexes_to_change:
            self.__df.at[index_to_change, self.__colnames[1]] = feature_id
            self.__df.at[index_to_change, self.__colnames[3]] = compactness
            self.__df.at[index_to_change, self.__colnames[5]] = points

    def update_compactness_table(self, what_to_dissolve, i):
        #aktualizuje tabele compactnes - tylko w wierszach w ktorych nastapila jakas zmiana po ostatnim polaczeniu
        feature = what_to_dissolve[0]
        neighbor = what_to_dissolve[1]
        #Usuniecie z tabeli rekrodow (feature, neighbor) oraz (neighbor,feature)
        to_delete = self.__compactness_table.loc[(self.__compactness_table['f'] == feature) & (self.__compactness_table['n'] == neighbor)]
        self.__compactness_table = self.__compactness_table.drop(to_delete.index)
        to_delete = self.__compactness_table.loc[(self.__compactness_table['n'] == feature) & (self.__compactness_table['f'] == neighbor)]
        self.__compactness_table = self.__compactness_table.drop(to_delete.index)

        #Podmiana wszystkich wskaznikow z sasiada na jego nowe ID (ID obiektu feature)
        self.__compactness_table.loc[self.__compactness_table['f'] == neighbor, 'f'] = feature
        self.__compactness_table.loc[self.__compactness_table['n'] == neighbor, 'n'] = feature
        #Wziecie rekordow z compactness table ktore maja w sobie ID feature (bo trzeba je na nowo przeliczyc)
        rows1 = self.__compactness_table.loc[(self.__compactness_table['f'] == feature)]
        rows2 = self.__compactness_table.loc[(self.__compactness_table['n'] == feature)]
        rows = pd.concat([rows1, rows2])
        #Sprawdzenie czy w rows nie ma duplikatów spowodowanych sąsiedztwem z jakimś poligonem i feature i neighbor:
        duplicates = rows[rows.duplicated(['f', 'n'])].index
        if len(duplicates) > 0:
            self.__compactness_table = self.__compactness_table.drop(duplicates)
            rows = rows.drop(duplicates)

        #Przeliczenie na nowo wartosci compactness w rows:
        for row_index in rows.index:
            feature_id = rows.at[row_index, 'f']
            neighbor_id = rows.at[row_index, 'n']
            feature = self.__df.loc[self.__df[self.__colnames[1]] == feature_id]
            neighbor = self.__df.loc[self.__df[self.__colnames[1]] == neighbor_id]
            compactness_score = self.__get_compactness_score(feature, neighbor)
            self.__compactness_table.at[row_index, 'c'] = compactness_score

    def save_results(self, filename):
        #zapisuje wynik algorytmu do pliku geojson
        df = self.__df.copy().dissolve(by=self.__colnames[1])
        df.to_file(filename, driver="GeoJSON")

    def dissolve_invaild_polygons(self):
        while True:
            self.__df['tempID'] = self.__df['oldID']
            all_vaild = True
            for index, row in self.__df.iterrows():
                if row.geometry.is_valid == False or len(row.geometry.interiors) > 0: 
                    neighbors = self.__df[~self.__df.geometry.disjoint(row.geometry)].index
                    to_dissolve=[]
                    exterior = row.geometry.exterior
                    poly_exterior = Polygon(exterior)
                    for n in neighbors:
                        if self.__df.at[n, 'geometry'].centroid.within(poly_exterior):
                            to_dissolve.append(n)
                    if index not in to_dissolve:
                        to_dissolve.append(index)
                    if len(to_dissolve) == 1:
                        to_dissolve=[]
                        line_exterior = LineString(exterior)
                        for n in neighbors:
                            boundary = self.__df.at[n, 'geometry'].boundary
                            if line_exterior.contains(boundary):
                                to_dissolve.append(n)
                    if len(to_dissolve) == 1:
                        to_dissolve=[]
                        for n in neighbors:
                            if self.__df.at[n, 'geometry'].centroid.within(self.__df.loc[index].geometry.envelope):
                                to_dissolve.append(n)
                        if index not in to_dissolve:
                            to_dissolve.append(index)
                    if len(to_dissolve) <= 1:
                        print("Znaleziono błędny poligon, ale nie udało się go naprawić w tej iteracji")
                    #Walidacja poligonów które mają się złączyć - czy przypadkiem któryś z nich nie stworzy multipoligonu
                    for t_d in to_dissolve.copy():
                        geom_to_be_dissolved = self.__df.at[t_d, 'geometry']
                        try:
                            coords1 = list(map(tuple, np.asarray(geom_to_be_dissolved.boundary.coords.xy).T))
                        except:
                            #Przypadek gdzie poligon jest zbudowany z multilinii:
                            coords1 = []
                            for g in row.geometry.boundary:
                                coords1 += list(map(tuple, np.asarray(g.coords.xy).T))
                        try:
                            coords2 = list(map(tuple, np.asarray(row.geometry.boundary.coords.xy).T))
                        except:
                            #Przypadek gdzie poligon jest zbudowany z multilinii:
                            coords2 = []
                            for g in row.geometry.boundary:
                                coords2 += list(map(tuple, np.asarray(g.coords.xy).T))
                        common_coords = set(coords1).intersection(set(coords2))
                        if len(common_coords) < 2:
                            to_dissolve.remove(t_d)
                            
                        
                    self.__df.loc[to_dissolve, "tempID"] = self.__df.at[to_dissolve[0], "tempID"]
                    all_vaild = False
            if all_vaild == True:
                self.__df['oldID'] = self.__df.index
                self.__df['newID'] = self.__df.index
                self.__df['ID'] = self.__df.index
                break
            self.__df = self.__df.dissolve(by='tempID')
            self.__df.index = np.arange(1, len(self.__df)+1)
            self.__df.index.names = ['Index']
# -*- coding: utf-8 -*-

import os
import csv
import math
import geopandas as gpd
import pandas as pd
from datetime import datetime, date

from python_scripts.region_maker.create_bricks import create_bricks
from python_scripts.algorythm.brick_creating_algorithm import brick_creating
from python_scripts.validate_by_area import validate_by_area

#################################################################################################################
#PARAMETRY:
CREATE_REGIONS = True #False oznacza że nie tworzymy nowych regionów tylko korzystamy z już przygotowanych
#pozwoli to zaoszczędzić czas w przypadku w którym zmieniamy niektóre parametry tworzenia cegiełek, ale nie zmieniamy regionów
#jeśli algorytm puszczany jest po raz pierwszy, należy ustawić wartość na True
DEBUG_LAYERS_MODE = True #Będą tworzone dodatkowe warstwy na poszczególnych krokach algorytmu DLA KAŻDEGO REGIONU. 
#Mają one pozwolić na podgląd zmian i decyzji wprowadzanych przez algorytm

#Układ ścieżek z danymi:
INPUT_DIR = os.getcwd() + "\\input"
PROCESSING_DIR = os.getcwd() + "\\processing"
OUTPUT_DIR = os.getcwd() + "\\output"

#Parametry dot. pliku z gminami:
GMINY = "gminy.shp"
GMINA_ID_COLNAME = "STATEXID"
GMINA_NAME_COLNAME = "NAME"
ADR_COLNAME = "punkty_adr"

#Parametry dot. pliku z adresami:
INPUT_POINTS = "adresy.shp"
FLATS_COLNAME = "mieszkania"
BUILDING_COLNAME = "gml_id"
STREET_COLNAME = "ulica"
HOUSE_NUMBER_COLNAME = "nr"

#Parametry dot. tworzenia cegiełek wewnątrz regionów:
BRICK_SIZE = 3000 #z ilu mieszkań ma się idealnie składać cegiełka?

# Parametry dot. tworzenia cegiełek wewnątrz regionów:
MINIMUM_POINTS_IN_REGION = 100 #Poligony będą się kleić ze sobą tak długo, aż nie przekroczą tego progu
#################################################################################################################

start_time = datetime.now()
dir_polygons_from_cutting_lines = PROCESSING_DIR + "\\polygons_from_cutting_lines"
dir_regions = PROCESSING_DIR + "\\regions"
if not os.path.exists(dir_regions):
    os.makedirs(dir_regions)
os.chdir(INPUT_DIR)
with open('wybrane_gminy.csv', "rt", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    gminy_id = list(reader)
with open('techniczna_a_gminy.csv', "rt", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    tech_a = list(reader)
gminy_id = [gmina[0] for gmina in gminy_id]

filename = os.path.splitext(GMINY)[0]
gminy_local_path = f'{filename}\\{GMINY}'
gminy_gdf_all = gpd.read_file(gminy_local_path)
#Usunięcie z gmin tych, które pędą podzielone - zrobienie miejsca na nowe cegiełki
gminy_gdf = gminy_gdf_all.loc[~gminy_gdf_all[GMINA_ID_COLNAME].isin(gminy_id)]
gminy_gdf['Brick_ID'] = gminy_gdf[GMINA_ID_COLNAME].values

gminy_gdf = gminy_gdf.explode()
not_unique_ids = gminy_gdf[GMINA_ID_COLNAME].values
for id in not_unique_ids:
    same_ids = gminy_gdf[gminy_gdf['Brick_ID'] == id].index
    if len(same_ids) > 1:
        count = 1
        for same_id in same_ids:
            gminy_gdf.at[same_id, 'Brick_ID'] = gminy_gdf.at[same_id, 'Brick_ID'] + "-" + str(count)
            count += 1

for gmina_id in gminy_id:
    parts = 1
    if [gmina_id] in tech_a:
        parts = 2
    original_gmina_id = gmina_id
    for part in range(parts):
        part += 1
        gmina_id = original_gmina_id
        gmina_id = str(gmina_id) + "__" + str(part)
        if CREATE_REGIONS == True:
            start_time_regions = datetime.now()
            create_bricks(MINIMUM_POINTS_IN_REGION, "polygons_from_cutting_lines" + gmina_id + ".json", "regions" + gmina_id + ".json", 
                dir_polygons_from_cutting_lines, dir_regions) 
            end_time_regions = datetime.now()
            delta_time_regions = (end_time_regions - start_time_regions)
            print("Czas trwania tworzenia regionów: " + str(delta_time_regions))

        input_region_polygons = "regions" + gmina_id + ".json"

        bricks = brick_creating(INPUT_POINTS, INPUT_DIR, dir_regions, FLATS_COLNAME, BUILDING_COLNAME, ADR_COLNAME,
                STREET_COLNAME, HOUSE_NUMBER_COLNAME,  BRICK_SIZE, input_region_polygons, 
                gmina_id, DEBUG_LAYERS_MODE)
        bricks[GMINA_ID_COLNAME] = original_gmina_id
        bricks[GMINA_NAME_COLNAME] = gminy_gdf_all[gminy_gdf_all[GMINA_ID_COLNAME] == original_gmina_id][GMINA_NAME_COLNAME].values[0]
        
        to_concat = [gminy_gdf, bricks]
        gminy_gdf = gpd.GeoDataFrame(pd.concat(to_concat, ignore_index=True, sort=False))


def round_float(x):
    if math.isnan(x) == False:
        return round(x)
    else:
        return x
gminy_gdf[ADR_COLNAME] = pd.array(gminy_gdf[ADR_COLNAME], dtype="Int64")
gminy_gdf[FLATS_COLNAME] = gminy_gdf[FLATS_COLNAME].apply(lambda x: round_float(x))
gminy_gdf[FLATS_COLNAME] = pd.array(gminy_gdf[FLATS_COLNAME], dtype="Int64")

os.chdir(PROCESSING_DIR)
gminy_gdf.crs = "EPSG:4326"
gminy_gdf.to_file("gminy_rozdzielone_przed_czyszczeniem.shp")

validate_by_area(gminy_gdf, gminy_gdf_all)

end_time = datetime.now()
delta_time = (end_time - start_time)
print("Czas trwania procesu: " + str(delta_time))
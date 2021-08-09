# -*- coding: utf-8 -*-
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import python_scripts.region_maker.bricks as b

def choose_what_to_dissolve(bricks, neighborhoods, no_need_to_check_anymore):
    best_pair = []
    if len(no_need_to_check_anymore) > 0:
        neighborhoods = np.delete(neighborhoods, no_need_to_check_anymore, 0)
    for neighborhood in neighborhoods:
        if neighborhood[1].size > 0:
            feature_id = neighborhood[0]
            if bricks.if_too_little_points(feature_id):    
                for neighbor_id in neighborhood[1]:
                    if bricks.if_cutline_is_not_crossed(feature_id, neighbor_id):
                        compactness_diffrence = bricks.get_compactness(feature_id, neighbor_id)
                        if len(best_pair) == 0 or compactness_diffrence < best_pair[2]:
                            best_pair = [feature_id, neighbor_id, compactness_diffrence]
            else:
                no_need_to_check_anymore.append(neighborhood[0]-1)
        else:
            no_need_to_check_anymore.append(neighborhood[0]-1)
    #przypadek w ktorym feature jest otoczony tylko poligonami ktore maja wspolne oldID:
    if len(best_pair) == 0:
        for neighborhood in neighborhoods:
            if neighborhood[1].size > 0:
                feature_id = neighborhood[0]
                if bricks.if_too_little_points(feature_id): 
                    for neighbor_id in neighborhood[1]:
                        compactness_diffrence = bricks.get_compactness(feature_id, neighbor_id)
                        if len(best_pair) == 0 or compactness_diffrence < best_pair[2]:
                            best_pair = [feature_id, neighbor_id, compactness_diffrence]
    if len(best_pair) != 0:
        return best_pair[0:2], no_need_to_check_anymore
    else:
        return None, no_need_to_check_anymore                                                                                          

def update_neighborhoods(bricks, neighborhoods, what_to_dissolve):
    feature_index = what_to_dissolve[0] -1
    neighbor_index = what_to_dissolve[1] -1
    feature_id = what_to_dissolve[0]
    neighbor_id = what_to_dissolve[1]
    
    #Poprawne uzupełnienie pola sasiadow obiektu
    neighborhoods[feature_index][1] = np.union1d(neighborhoods[neighbor_index][1], neighborhoods[feature_index][1])
    neighborhoods[feature_index][1] = neighborhoods[feature_index][1][neighborhoods[feature_index][1] != neighbor_id]
    neighborhoods[feature_index][1] = neighborhoods[feature_index][1][neighborhoods[feature_index][1] != feature_id]
    #Usuniecie sasiadow przylaczanego sasiada
    neighborhoods[neighbor_index][1] = []
    #Podmiana wskaznikow z usunietego sasiada na jego nowe ID (ID obiektu)
    neighborhoods = [[neighborhood[0], np.where(neighborhood[1]==neighbor_id ,feature_id,neighborhood[1])] for neighborhood in neighborhoods]
    neighborhoods = [[neighborhood[0],np.unique(neighborhood[1])] for neighborhood in neighborhoods]
    return(neighborhoods)


###########
#ZALOZENIA!!
#   laczymy poligony w ktorym przynajmniej jeden ma liczbe punktow mniejsza niz minimalna
#   chcemy by w miare mozliwosci nowe poligony były jak najbardziej kuliste, tzn. mialy jak najlepszy spadek compactness w porowananiu ze stanem poprzednim

def create_bricks(min_points, input_filename, output_filename, input_dir, output_dir):
    COLNAMES = ["ID", "newID", "comp", "newcomp", "points", "newpoints", "oldID"]
    MINIMUM_POINTS = min_points
    INPUT_FILENAME = input_filename
    OUTPUT_FILENAME = output_filename
    INPUTFOLDER = input_dir
    OUTPUTFOLDER = output_dir

    os.chdir(INPUTFOLDER)

    df = gpd.read_file(INPUT_FILENAME)
    df.index += 1 
    bricks = b.Bricks(df, COLNAMES, MINIMUM_POINTS)

    bricks.dissolve_invaild_polygons()
    neighborhoods = bricks.get_neighborhoods()
    print("Topologia gotowa!")
    bricks.create_compactness_table(neighborhoods)
    print("Tabela compactness gotowa!")
    
    no_need_to_check_anymore = []
    i = 1
    while True:
        what_to_dissolve, no_need_to_check_anymore = choose_what_to_dissolve(bricks, neighborhoods, no_need_to_check_anymore)
        if what_to_dissolve == None:
            break
        print("Najlepsza para wybrana! " + str(what_to_dissolve))
        bricks.update_dataframe(what_to_dissolve)
        print("Update tabeli gotowy!")
        neighborhoods = update_neighborhoods(bricks, neighborhoods, what_to_dissolve)
        print("Nowi sasiedzi zaktualizowani")
        bricks.update_compactness_table(what_to_dissolve, i)
        print("Tabela compactness zaktualizowana!")
        print("Liczba iteracji:")
        print(i)
        i+=1
    os.chdir(OUTPUTFOLDER)
    bricks.save_results(OUTPUT_FILENAME)
    print("Skrypt wykonany")
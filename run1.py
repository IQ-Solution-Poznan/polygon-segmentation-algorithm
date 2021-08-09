# -*- coding: utf-8 -*-

import grass.script as grass
import os
import shutil
import csv

GMINY_ID_COL = 'STATEXID'
SNAP_VALUE = 0.0000008

dir = os.getcwd()
os.chdir(dir + "/input")

#Branie pod uwage tylko interesujacych nas gmin:
with open('wybrane_gminy.csv', 'r+', encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    gminy = list(reader)
with open('techniczna_a_gminy.csv', 'r+', encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    tech_a = list(reader)

os.chdir(dir + "/input")
mapsetname = 'cegielkiMapset'
grass.run_command('g.mapset', flags='c', mapset=mapsetname)
#Wczytanie plikow shp - należy dostosować do swoich potrzeb:
grass.run_command('v.in.ogr', input='gminy\\gminy.shp', snap=SNAP_VALUE, output='gminy', overwrite=True)
grass.run_command('v.in.ogr', input='railways\\railways.shp', output='railways', overwrite=True)
grass.run_command('v.in.ogr', input='waterways\\waterways.shp', output='waterways', overwrite=True)
grass.run_command('v.in.ogr', input='roads\\roads.shp', output='roads', overwrite=True)
grass.run_command('v.in.ogr', input='lakes\\lakes.shp', output='lakes', overwrite=True)
grass.run_command('v.in.ogr', input='adresy\\adresy.shp', output='raw_points', overwrite=True)
grass.run_command('v.in.ogr', input='techniczna_A\\techniczna_A.shp', output='tech_a', overwrite=True)
grass.run_command('v.in.ogr', input='techniczna_B\\techniczna_B.shp', output='tech_b', overwrite=True)



#Petla - operacje beda wykonywane dla kazdej gminy z listy
for gmina in gminy:
    gmina = gmina[0]    

    if [gmina] in tech_a:
        #Wydobycie poligonu gminy i przyciecie nimi budynkow
        query = "CAST("+ GMINY_ID_COL + " AS int) = " + "CAST("+ gmina + " AS int)"
        grass.run_command('v.extract', input='gminy', output='bricks', where = query, overwrite=True)
        
        #przecięcie liniami technicznymi A:
        grass.run_command('v.to.lines', input='bricks', out='dissolved_bricks_as_linesA', overwrite=True)
        grass.run_command('v.patch', input='dissolved_bricks_as_linesA,tech_a', output='all_lines_patchedA', overwrite=True)
        grass.run_command('v.clean', input='all_lines_patchedA', tool='snap', threshold=SNAP_VALUE, output='all_lines_patched_cleanedA', overwrite=True)
        grass.run_command('v.clean', input='all_lines_patched_cleanedA', type='line', tool='break', output='all_lines_cleanedA', overwrite=True)
        grass.run_command('v.type', input='all_lines_cleanedA', out='all_lines_empty_polygonA', 
                            from_type='line', to_type='boundary', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygonA', type='boundary', tool='rmdupl', output='all_lines_empty_polygon1A', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon1A', type='boundary', tool='rmline', output='all_lines_empty_polygon2A', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon2A', type='boundary', tool='break', output='all_lines_empty_polygon3A', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon3A', type='boundary', tool='rmdangle', threshold='-1',
                        output='all_lines_cleaned_boundariesA', overwrite=True)
        grass.run_command('v.centroids', input='all_lines_cleaned_boundariesA', output='all_lines_result_ver1A', overwrite=True)
        grass.run_command('v.db.addtable', map='all_lines_result_ver1A')

        query1 = "CAST(cat AS int) == 1"
        grass.run_command('v.extract', input='all_lines_result_ver1A', output='bricks1', where = query1, overwrite=True)
        query2 = "CAST(cat AS int) == 2"
        grass.run_command('v.extract', input='all_lines_result_ver1A', output='bricks2', where = query2, overwrite=True)
        parts = 2
    else:
        #Wydobycie poligonu gminy i przyciecie nimi budynkow
        query = "CAST("+ GMINY_ID_COL + " AS int) = " + "CAST("+ gmina + " AS int)"
        grass.run_command('v.extract', input='gminy', output='bricks1', where = query, overwrite=True)
        parts = 1
    
    for part in range(parts): 
        part += 1
        grass.run_command('v.distance', from_ ='raw_points', from_type='point', to='bricks'+str(part), to_type='area', output='points', 
            dmax=0, overwrite=True)
        
        #Stworzenie jedenego poligonu o zasiegu wszystkich cegielek
        grass.run_command('v.db.addcolumn', map='bricks'+str(part), columns='a integer')
        grass.run_command('v.dissolve', input='bricks'+str(part), output='dissolved_bricks', column='a', overwrite=True)
        grass.run_command('v.db.addtable', map='dissolved_bricks', key='ID')


        grass.run_command('v.to.lines', input='lakes', out='lakes_as_lines', overwrite=True)
        #Polaczenie drog, kolei i ciekow do jednej warstwy:
        grass.run_command('v.patch', input='waterways,roads,railways,lakes_as_lines,tech_b', output='cutlines', overwrite=True)

        #Wyczyszczenie linii tnacych:
        grass.run_command('v.clean', input='cutlines', type='line', tool='rmdupl', output='cutlines_cleaned1', overwrite=True)
        grass.run_command('v.clean', input='cutlines_cleaned1', type='line', tool='rmline', output='cutlines_cleaned', overwrite=True)

        #Intersect:
        grass.run_command('v.overlay', ainput='cutlines_cleaned', atype='line', binput='dissolved_bricks', btype='area', olayer = '0,1,0',
                        operator='and', output='cutting_lines_intersected', overwrite=True)

        #Przeciecie poligonu liniami tnacymi:
        grass.run_command('v.to.lines', input='dissolved_bricks', out='dissolved_bricks_as_lines', overwrite=True)
        grass.run_command('v.patch', input='dissolved_bricks_as_lines,cutting_lines_intersected', output='all_lines_patched', overwrite=True)
        grass.run_command('v.clean', input='all_lines_patched', tool='snap', threshold=SNAP_VALUE, output='all_lines_patched_cleaned', overwrite=True)
        grass.run_command('v.clean', input='all_lines_patched_cleaned', type='line', tool='break', output='all_lines_cleaned', overwrite=True)
        grass.run_command('v.type', input='all_lines_cleaned', out='all_lines_empty_polygon', 
                            from_type='line', to_type='boundary', overwrite=True)

        grass.run_command('v.clean', input='all_lines_empty_polygon', type='boundary', tool='rmdupl', output='all_lines_empty_polygon1', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon1', type='boundary', tool='rmline', output='all_lines_empty_polygon2', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon2', type='boundary', tool='break', output='all_lines_empty_polygon3', overwrite=True)
        grass.run_command('v.clean', input='all_lines_empty_polygon3', type='boundary', tool='rmdangle', threshold='-1',
                        output='all_lines_cleaned_boundaries', overwrite=True)
        grass.run_command('v.centroids', input='all_lines_cleaned_boundaries', output='all_lines_result_ver1', overwrite=True)
        
        #Poprawki:
        grass.run_command('v.overlay', ainput='dissolved_bricks', atype='area', binput='all_lines_result_ver1', btype='area', olayer = '0,1,0',
                        operator='not', output='all_lines_result111', overwrite=True)
        try:
            grass.run_command('v.overlay', ainput='all_lines_result_ver1', atype='area', binput='all_lines_result111', btype='area',
                            operator='or', output='all_lines_result', overwrite=True)
            grass.run_command('v.db.droptable', map='all_lines_result', flags='f')
        except:
            grass.run_command('v.centroids', input='all_lines_cleaned_boundaries', output='all_lines_result', overwrite=True)
        
        #Przygotowanie tabeli atrybutow:
        grass.run_command('v.db.addtable', map='all_lines_result', key='ID')
        grass.run_command('v.db.addcolumn', map='all_lines_result', 
                        columns='newID integer,comp double precision,points integer, newcomp double precision,newpoints integer, oldID integer')
        grass.run_command('v.vect.stats', points='points', areas='all_lines_result', count_column='points')
        grass.run_command('v.vect.stats', points='points', areas='all_lines_result', count_column='newpoints')
        grass.run_command('v.to.db', map='all_lines_result', option='compact', columns='comp')
        grass.run_command('v.db.update', map='all_lines_result', column='newID', query_column='ID')
        grass.run_command('v.db.update', map='all_lines_result', column='oldID', query_column='ID')
        grass.run_command('v.db.update', map='all_lines_result', column='newcomp', query_column='comp')
        
        #Zwrocenie wynikow:
        directory = dir + "/processing/polygons_from_cutting_lines"
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.chdir(dir + "/processing/polygons_from_cutting_lines")
        filename = 'polygons_from_cutting_lines' + gmina + "__" + str(part) + '.json'
        if os.path.isfile('./'+filename):
            os.remove(filename)
        grass.run_command('v.out.ogr', input='all_lines_result', output=filename, format='GeoJSON', overwrite=True)

#Usuniecie mapsetu:
grass.run_command('g.mapset', mapset='PERMANENT')
shutil.rmtree(dir + '/grass/mapset4326/' + mapsetname + "/")

print("Skrypt wykonany")

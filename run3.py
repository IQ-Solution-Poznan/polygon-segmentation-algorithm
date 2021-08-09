# -*- coding: utf-8 -*-

import grass.script as grass
import os
import shutil
from datetime import date

SNAP_VALUE = 0.0000008
INPUT = 'gminy_rozdzielone_przed_czyszczeniem.shp'

dir = os.getcwd()
output_dir = dir + '/output/'
history_dir = dir + "/output_history"
if os.path.isdir(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)
if not os.path.exists(history_dir):
    os.makedirs(history_dir)

#Przechowywujemy w historii max 3 archiwalne wyniki
os.chdir(history_dir)
files_in_history = os.listdir(history_dir)
shapes_in_history = [file for file in files_in_history if "shp" in file]
if len(shapes_in_history) > 3:
    file_to_delete = sorted(shapes_in_history)[0]
    file_to_delete_date = os.path.splitext(file_to_delete)[0].split("_")[2]
    for file in files_in_history:
        if file_to_delete_date in file:
            os.remove(file)

os.chdir(dir + "/processing")

mapsetname = 'outputmapset'
grass.run_command('g.mapset', flags='c', mapset=mapsetname)

grass.run_command('v.in.ogr', input=INPUT, snap=SNAP_VALUE, output='out', overwrite=True)

os.chdir(output_dir)
grass.run_command('v.out.ogr', flags='s', input='out', output=f'gminy_rozdzielone_{date.today()}.shp', format="ESRI_Shapefile", overwrite=True)
os.chdir(history_dir)
grass.run_command('v.out.ogr', flags='s', input='out', output=f'gminy_rozdzielone_{date.today()}.shp', format="ESRI_Shapefile", overwrite=True)

grass.run_command('g.mapset', mapset='PERMANENT')
shutil.rmtree(dir + '/grass/mapset4326/' + mapsetname + "/")
print("Skrypt wykonany")
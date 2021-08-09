# -*- coding: utf-8 -*-

import geopandas as gpd
from shapely.geometry import Polygon

def copy_attributes_by_location(points, polygons, attributes):
    #Stworzenie nowych kolumn, które potem będziemy wypełniać wartościami
    for attribute in attributes:
        polygons[attribute] = None
    
    #Żeby przyśpieszyć proces, stworzyłem zbiór indexów poligonów które zostały jeszcze sparowane z żadnym punktem
    #Początkowo zbiór ten równa się ilości poligonów w regionie, na końcu każdej iteracji równa się 0
    polygons_unassigned = set(polygons.index)

    #Sprawdzamy dla każdego punktu i każdego poligonu czy punkt leży w poligonie (.within)
    for point_index, point_geometry in zip(points.index, points.geometry):
        for polygon_index, polygon_geometry in zip(polygons.index, polygons.geometry):
            #Jeśli index poligonu nie jest w zbiorze polygons_unassigned, to znaczy że jego atrybuty zostały już wypełnione
            #Nie ma więc sensu sprawdzać czy punkt się w nim zawiera i z góry możemy go odrzucić (każdy poligon ma w sobie tylko 1 punkt)
            if polygon_index in polygons_unassigned:
                if point_geometry.within(polygon_geometry):
                    #Jeśli udało się znaleźć punkt leżący w poligonie, to index poligonu usuwany jest ze zbioru polygons_unassigned
                    polygons_unassigned.remove(polygon_index)
                    #A samemu poligonowi przypisywane są wartości skopiowane z aktualnego punktu
                    for attribute in attributes:
                        polygons.at[polygon_index, attribute] = points.at[point_index, attribute]
                    #Następnie przerywany wewnętrzną pętlę - mamy już znaleziony poligon dla tego punktu, możemy przejść do kolejnego
                    break

    return polygons
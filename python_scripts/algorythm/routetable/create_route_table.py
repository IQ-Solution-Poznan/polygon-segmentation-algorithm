# -*- coding: utf-8 -*-

from python_scripts.algorythm.routetable.route_table_lib import RouteTable

def create_route_table(pointset):
    
    routetable = RouteTable(pointset)

    #wyodrebnienie koorydantow xy z geodataframe
    routetable.read_coords()
    #stworzenie tabeli w oparciu o osrm
    routetable.create_table()
    routetable.change_none_to_numbers()
    #ujednolicenie czasu dla obu kierunkow (przypisanie w obu kierunkach wiekszej/mniejszej/średniej z wartosci)
    routetable.make_symmetric()
    
    route_table = routetable.return_table()
    return route_table
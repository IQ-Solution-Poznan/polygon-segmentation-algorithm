#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  1 09:44:34 2019

@author: jarekj
"""
import numpy as np
import os
import json


#%%

class topoparser():
    '''
    parsuje tylko poligony z jedną warstwą
    '''
    def __init__(self,file=None,topo=None):
        if topo is not None:
            self.__topojson = topo
        else:
            self.__topojson = json.load(open(file,"rb"))
        self.__arcs = self.__topojson['arcs']
        self.__topopairs = np.full((len(self.__arcs),2),-1)
        self.__layername = list(self.__topojson['objects'].keys())[0]
        self.__neiborhoods = []
        
         
    def __get_arcs(self,arc,objid):
        ''' defnicje łuków z wartością ujemną to odwrotna wartość 
        w systemie dopełnieniowym do dwóch
        aby uzyskać łuk należy wykonac bitwise negation
        '''
        if arc < 0:
            self.__topopairs[~arc][1] = objid  # bitwise negation
        else:
            self.__topopairs[arc][0] = objid
    
    def __convert_to_pairs(self):
        objects = self.__topojson['objects'][self.__layername]['geometries']
        
        for objid,obj in enumerate(objects):
            for ring in obj['arcs']:
                for arc in ring:
                    if isinstance(arc, list):
                        for i in arc:
                            self.__get_arcs(i,objid)
                    else:
                        self.__get_arcs(arc,objid)
            
    def __get_neighbors(self,obj,objid):
        neighbors = []
        for ring in obj['arcs']:
            for arc in ring:
                if isinstance(arc, list):
                        for i in arc:
                            i = ~i if i < 0 else i
                            pair = self.__topopairs[i]
                            if pair[0] != objid and pair[1] !=objid:
                                raise Exception("Something wrong with {}".format(objid))
                            if pair[0] == pair[1]:
                                raise Exception("Something wrong with {}: same polygons".format(objid))
                            index_to_append = pair[1] if pair[0]==objid else pair[0]
                            if index_to_append >-1:
                                neighbors.append(index_to_append)
                else:
                    arc = ~arc if arc < 0 else arc
                    pair = self.__topopairs[arc]
                    if pair[0] != objid and pair[1] !=objid:
                        raise Exception("Something wrong with {}".format(objid))
                    if pair[0] == pair[1]:
                        raise Exception("Something wrong with {}: same polygons".format(objid))
                    index_to_append = pair[1] if pair[0]==objid else pair[0]
                    if index_to_append >-1:
                        neighbors.append(index_to_append)
        return np.array(neighbors)
                
    def __convert_to_neighborhoods(self):
        objects = self.__topojson['objects'][self.__layername]['geometries']
        for objid,obj in enumerate(objects):
            self.__neiborhoods.append(self.__get_neighbors(obj,objid))
            
    
    @property
    def pairs(self):
        return self.__topopairs
    
    @property
    def neighborhoods(self):
        return self.__neiborhoods
    
    def parse(self):
        self.__convert_to_pairs()
        self.__convert_to_neighborhoods()

#%%       





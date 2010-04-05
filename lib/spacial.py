#!/usr/bin/python
# -*- coding: utf-8 -*-
u"""

"""

__version__ = '$Id: spacial.py 575 2009-09-08 17:55:41Z dr0iddr0id $'

import collections

class Space(object):

    def __init__(self, cell_size, items=[]):
        self.cell_width = cell_size[0]
        self.cell_height = cell_size[1]
        
        self.cells = collections.defaultdict(list)

        self.add(items)


    def add(self, items):
        hits = []
        for item in items:
            radius = item.bounding_radius
            pos = item.position
            xmin = (pos.x - radius) // self.cell_width
            xmax = (pos.x + radius) // self.cell_width
            ymin = (pos.y - radius) // self.cell_height
            ymax = (pos.y + radius) // self.cell_height

            bhits = []
            if xmin==xmax and ymin==ymax:
                bhits.extend(self.cells[(xmin,ymin)])
                self.cells[(xmin,ymin)].append(item)
            else:
                for cellx in range(xmin, xmax+1):
                    for celly in range(ymin, ymax+1):
                        bhits.extend(self.cells[(cellx, celly)])
                        self.cells[(cellx,celly)].append(item)
            hits.append((item, bhits))
        return hits

    def remove(self, items):
#        for item in items:
#            for buck in self.cells.values():
#                if item in buck:
#                    buck.remove(item)
        for item in items:
            radius = item.bounding_radius
            pos = item.position
            xmin = (pos.x - radius) // self.cell_width
            xmax = (pos.x + radius) // self.cell_width
            ymin = (pos.y - radius) // self.cell_height
            ymax = (pos.y + radius) // self.cell_height
            try:
                if xmin==xmax and ymin==ymax:
                    self.cells[(xmin,ymin)].remove(item)
                else:
                    for cellx in range(xmin, xmax+1):
                        for celly in range(ymin, ymax+1):
                            self.cells[(cellx, celly)].remove(item)
            except:
                pass

                    
    def hit(self, items):
        hits = []
        cells = self.cells
        for item in items:
            radius = item.bounding_radius
            xmin = (item.position.x - radius) // self.cell_width
            xmax = (item.position.x + radius) // self.cell_width
            ymin = (item.position.y - radius) // self.cell_height
            ymax = (item.position.y + radius) // self.cell_height
            bhits = []
            if xmin==xmax and ymin==ymax:
                self.cells[(xmin,ymin)].append(item)
            else:
                for cellx in range(xmin, xmax+1):
                    for celly in range(ymin, ymax+1):
                        bhits.extend(cells[(cellx,celly)])
            hits.append(bhits)
        return hits

                    
                    
                    
#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: obstacle.py 569 2009-09-07 03:24:42Z DLacewell $'

import random

import pyglet
from pyglet.gl import *
from lib.vectors import Vec3
from lib.entity import Entity
from lib.events import Signal
from lib.util import uuid, TextureBindGroup

import cerealizer

#------------------------------------------------------------------------------

class Obstacle(object):

    def __init__(self, position, size):
        pass

#------------------------------------------------------------------------------

class SerialPolygon(object):
    def __init__(self, polygon):
        self.vertices = polygon.vertices
        self.texture_name = polygon.texture_name
cerealizer.register(SerialPolygon)

class Polygon(Entity):

    DEFAULT_TEXTURE = "data/textures/level/bluerock.png"

    def __init__(self, scene, batch=None, serial=None, texture_pair=None):
        super(Polygon, self).__init__()
        self.scene = scene
        self.vertices = []
        self.edges = []
        self.normals = []
        self.uvmap = []
        self.batch = batch or pyglet.graphics.Batch()
        self.pvl = self.batch.add(1, pyglet.gl.GL_TRIANGLES, None,
                                 ('v2f', (0, 0)),
                                 ('t2f', (0.0, 0.0)),
                                 ('c3f', (0, 0, 0)))
        #self.gvl = self.batch.add(1, pyglet.gl.GL_LINE_STRIP, None,
        #                          ('v2f', (-100, -100)),
        #                          ('c3f', (0, 0, 0)))

        self.bacthopen = pyglet.graphics.Batch()
        self.pvlopen = self.bacthopen.add(1, pyglet.gl.GL_POLYGON, None,
                         ('v2f', (0, 0)),
                         ('t2f', (0.0, 0.0)),
                         ('c3f', (0, 0, 0)))
        self.gvlopen = self.bacthopen.add(1, pyglet.gl.GL_POINTS, None,
                                  ('v2f', (-100, -100)),
                                  ('c3f', (0, 0, 0)))
        if serial:
            self.load_polygon(serial)
        elif texture_pair:
            self.set_texture(texture_pair)
        else:
            texture_pair = (self.DEFAULT_TEXTURE, pyglet.image.load(self.DEFAULT_TEXTURE).texture)
            self.set_texture(texture_pair)
            
            
        
    def set_texture(self, texture):
        self.texture_name = texture[0]
        self.pvl.delete()
        self.pvl = self.batch.add(1, pyglet.gl.GL_TRIANGLES, TextureBindGroup(texture[1]),
                                 ('v2f', (0, 0)),
                                 ('t2f', (0.0, 0.0)),
                                 ('c3f', (0, 0, 0)))
        self.update_points2()
        
    def load_polygon(self, serial):
        self.vertices = serial.vertices
        print "Loading poly, ", self.vertices
        texture_pair = self.scene.get_texture(serial.texture_name)
        self.set_texture(texture_pair)
        
        
    def get_serialized(self):
        return SerialPolygon(self)
                                  
    def update_uvmap(self):
        v = self.vertices[0]
        xmin = xmax = v.x
        ymin = ymax = v.y
        
        for v in self.vertices:
            xmin = min(xmin, v.x)
            xmax = max(xmax, v.x)
            ymin = min(ymin, v.y)
            ymax = max(ymax, v.y)
            
        w = max(1.0, xmax - xmin)
        h = max(1.0, ymax - ymin)
        # (x-x_min)/w, (y-y_min)/h
        self.uvmap = []
        for v in self.vertices:
            x = v.x / 128 #(v.x - xmin)/w
            y = v.y / 128 #(v.y - ymin)/h
            
            self.uvmap.append([x, y])
        #self.uvmap.extend([self.uvmap[-2], self.uvmap[-1]])
        if __debug__: print len(self.vertices), len(self.uvmap)
        if __debug__: print [(v.x, v.y) for v in self.vertices]
        if __debug__: print self.uvmap
        return self.uvmap    
        
    def update_colors(self):
        colors = []
        #for guide in reversed(self.vertices):
        for guide in self.vertices:
            screen = guide + self.scene.campos
            colors.extend([screen.x / 400.0, .8, screen.y / 300.0])
        #self.gvl.colors = colors
        
    def update_points2(self):
        self.position = sum(self.vertices, Vec3(0,0)) / float(len(self.vertices))
        if len(self.vertices) > 2:
            self.bounding_radius = 0
            for idx, vertex in enumerate(self.vertices):
                v = (vertex - self.position).length
                if v > self.bounding_radius:
                    self.bounding_radius = v
        
        self.update_uvmap()            
        
        gpoints = []            
        points = []
        colors = []
        for vertex in self.vertices:
            gpoints.extend([vertex.x, vertex.y])
            screen = vertex + self.scene.campos
            colors.extend([screen.x / 400.0, .6, screen.y / 300.0])
            
        #self.gvl.resize(len(gpoints) / 2)
        #self.gvl.vertices = gpoints
        #self.gvl.colors = colors
        
        tpoints = []
        tuvpoints = []
        tcolors = []
        for idx, vertex in enumerate(self.vertices):
            if idx < 2: 
                continue
            else:
                tpoints.extend([
                    self.vertices[0].x, self.vertices[0].y,
                    self.vertices[idx - 1].x, self.vertices[idx - 1].y,
                    self.vertices[idx].x, self.vertices[idx].y
                ])
                tuvpoints.extend([
                    self.uvmap[0][0], self.uvmap[0][1],
                    self.uvmap[idx - 1][0], self.uvmap[idx - 1][1],
                    self.uvmap[idx][0], self.uvmap[idx][1],
                ])
                tcolors.extend([
                    colors[0], colors[1], colors[2],
                    colors[(idx-1)*2], colors[((idx-1)*2)+1], colors[((idx-1)*2)+2],
                    colors[idx*2], colors[idx*2 + 1], colors[idx*2 + 2]
                ])
            
        #print "Vertices: ", len(self.vertices), self.vertices
        #print "TPoints: ", len(tpoints), tpoints
        #print "TColors: ", len(tcolors), tcolors
                
        self.pvl.resize(len(tpoints) / 2)
        self.pvl.vertices = tpoints
        self.pvl.tex_coords = tuvpoints
        self.pvl.colors = tcolors
        return True
        
    def update_points(self):
        # TODO: This should take one point (the changed point) and only update its neighbors.
        self.position = sum(self.vertices, Vec3(0,0)) / float(len(self.vertices))
        if len(self.vertices) > 2:
            self.bounding_radius = 0
            for idx, vertex in enumerate(self.vertices):
                v = (vertex - self.position).length
                if v > self.bounding_radius:
                    self.bounding_radius = v

        points = []
        gpoints = []
        colors = []
        #for guide in reversed(self.vertices):
        for guide in self.vertices:
            gpoints.extend([guide.x, guide.y])
            screen = guide + self.scene.campos
            colors.extend([screen.x / 400.0, .6, screen.y / 300.0])
            
        self.gvl.resize(len(gpoints) / 2)
        self.gvl.vertices = gpoints
        self.gvl.colors = colors
        self.gvlopen.resize(len(gpoints) / 2)
        self.gvlopen.vertices = gpoints
        self.gvlopen.colors = colors

        points = gpoints
        if points:
            color = [1., 1., 1.]
            #points.extend([gpoints[-2], gpoints[-1]])
            self.pvl.resize(len(points) / 2 )
            self.pvl.vertices = points
            self.pvl.colors = color * (len(points) / 2)
            self.pvl.tex_coords = self.update_uvmap()
            self.pvlopen.resize(len(points) / 2 )
            self.pvlopen.vertices = points
            self.pvlopen.tex_coords = self.uvmap
            self.pvlopen.colors = color * (len(points) / 2)
            
            return True

    def add_vertex(self, x, y):
        # first three point dont need check, they always form a valid convec triangle
        vertex = Vec3(x, y)
        self.vertices.append(vertex)
        if not self.check_vertex_valid(): 
            self.vertices.remove(vertex)
            return False
        self.update_points2()
        return True

    def remove_vertex(self, vertex):
        if vertex in self.vertices:
            self.vertices.remove(vertex)
        self.update_points2()

    def move_vertex(self, vertex, x, y):
        if vertex in self.vertices:
            old_x = vertex.x
            old_y = vertex.y
            vertex.x = x
            vertex.y = y
            # first three point dont need check, they always form a valid convec triangle
            if not self.check_vertex_valid(): 
                vertex.x = old_x
                vertex.y = old_y
                return False
            self.update_points2()
            return True

    def check_vertex_valid(self):
        if len(self.vertices) > 3:
            for idx, vertex in enumerate(self.vertices):
                #print 'check vertex', vertex, self.vertices[idx - 1], self.vertices[idx - 2]
                edge2 = self.vertices[idx - 1] - self.vertices[idx - 2]
                edge1 = vertex - self.vertices[idx - 1]
                #print 'check', edge2, edge1, edge2.cross(edge1).z
                if edge2.cross(edge1).z < 0:
                    print 'Poly failed!', idx
                    return False
        return True

    def draw(self):
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glLineWidth (5.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture.id);
        if self.vertices:
            pyglet.gl.glPointSize(5)
            self.batch.draw()
        glDisable(GL_TEXTURE_2D)
        glLineWidth (1.0)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        
    def draw_open(self):
            glColor4f(1.0, 1.0, 1.0, 1.0)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture.id);
            if self.vertices:
                pyglet.gl.glPointSize(5)
                self.bacthopen.draw()
            glDisable(GL_TEXTURE_2D)
    def is_point_in(self, x, y):
        # code by Randolph Franklin
        # taken from: http://local.wasp.uwa.edu.au/~pbourke/geometry/insidepoly/
        
        # TODO: test if this works correctly!
        c = 0
        for idx, vertex in enumerate(self.vertices):
            pvertex = self.vertices[idx - 1]
            ypi = vertex.y
            ypj = pvertex.y
            if((((ypi <= y) and (y < ypj)) or
            ((ypj <= y) and (y < ypi))) and
            (x < (pvertex.x - vertex.x) * (y - ypi) / (ypj - ypi) + vertex.x)):
                c = not c
        return c
# original C code:        
#    int pnpoly(int npol, float *xp, float *yp, float x, float y)
#    {
#      int i, j, c = 0;
#      for (i = 0, j = npol-1; i < npol; j = i++) {
#        if ((((yp[i] <= y) && (y < yp[j])) ||
#             ((yp[j] <= y) && (y < yp[i]))) &&
#            (x < (xp[j] - xp[i]) * (y - yp[i]) / (yp[j] - yp[i]) + xp[i]))
#          c = !c;
#      }
#      return c;
#    }
        
    
    def update(self, dt):
        pass

        
#------------------------------------------------------------------------------
import math

class SerialTrigger(object):
    def __init__(self, trigger):
        self.position = trigger.position
        self.bounding_radius = trigger.bounding_radius
        self.uuid = trigger.uuid

cerealizer.register(SerialTrigger)


class Trigger(Signal):
    """
    OneShotTrigger.
    
    Trigger that fires only once, then need a reset to fire again.
    
    Listeners can be added as to a Signal (+=, -=, etc).
    
    Handler signature is:
    
    on_trigger(source_trigger) # so the handler can manipulate the trigger
    
    The collision detection will have to fire it.
    
    """

    READY, FIRED = range(2)

    def __init__(self, position, radius, serial=None, batch=None):
        super(Trigger, self).__init__("Trigger")
        self.position = position
        self.bounding_radius = radius
        self.state = self.READY
        self.uuid = uuid()
        if serial:
            self.position = serial.position
            self.bounding_radius = serial.bounding_radius
            self.uuid = serial.uuid
            
        self.batch = batch or pyglet.graphics.Batch()
        self.cvl = self.batch.add(1, pyglet.gl.GL_POINTS, None,
                                 ('v2f', (0, 0)),
                                 ('c3f', (0, 0, 0)))
        self.update_points()
            

    def get_serialized(self):
        return SerialTrigger(self)
        
    def update_points(self):
        points = [self.position.x, self.position.y]
        colors = [.6, .48, .36] * 101
        r = self.bounding_radius       
        for i in xrange(100):
            phase = 2 * math.pi / 100 * i
            points.extend((self.position.x + r * math.sin(phase), self.position.y + r * math.cos(phase)))
            
        self.cvl.resize(len(points) / 2)
        self.cvl.vertices = points
        self.cvl.colors = colors


    def fire(self):
        if self.state == self.READY:
            self.state = self.FIRED
            # fire the event
            super(Trigger, self).fire(self)
        
    def reset(self):
        self.state = self.READY

    def draw(self):
        if __debug__:
            pyglet.gl.glPointSize(10)
            self.batch.draw()
        else:
            pass
            

#------------------------------------------------------------------------------

def test():

    p = Polygon()
    p.add_vertex(0, 0)
    p.add_vertex(5, 5)
    p.add_vertex(10, 0)
    print p.add_vertex(10, 20)
    
    p = Polygon()
    p.add_vertex(0, 0)
    p.add_vertex(10, 0)
    p.add_vertex(5, 5)
    

    print p.add_vertex(10, 20)




cerealizer.register(Polygon)












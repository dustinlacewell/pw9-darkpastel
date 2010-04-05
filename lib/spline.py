#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: run_game.py 218 2009-07-18 20:44:59Z dr0iddr0id $'

import pyglet
from pyglet.gl import *
from vectors import Vec3
from lib.flock import Flock
from lib.util import uuid
import cerealizer

class SerialSpline(object):
    def __init__(self, spline):
        self.kind = spline.kind
        self.guides = spline.guides
        self.uuid = spline.uuid
        self.trigger_uuids = spline.trigger_uuids
        
cerealizer.register(SerialSpline)

class Spline:
    WHITE = 0
    BLACK = 1
    CAMERA = 2
    # Would like to get rid of the Vector2d dependency.
    # Need to clean up the code and generalize colors.
    # Possilby make guides a class.
    def __init__(self, scene, batch=None, kind=0, serial=None):
        self.uuid = uuid()
        self.kind = kind
        self.scene = scene
        self.guides = []
        self.trigger_uuids = [] # needed to connect to correct trigger after serialization
        self.batch = batch or pyglet.graphics.Batch()
        self.pvl = self.batch.add(1, pyglet.gl.GL_LINE_STRIP, None,
                                 ('v2f', (0, 0)),
                                 ('c3f', (0, 0, 0)))
        self.gvl = self.batch.add(1, pyglet.gl.GL_POINTS, None,
                                  ('v2f', (-100, -100)),
                                  ('c3f', (0, 0, 0)))
        if serial:
            self.load_serial(serial)
    
    def load_serial(self, serial):
        #self.uuid = serial.uuid
        self.kind = serial.kind
        self.guides = serial.guides
        self.update_points()
        self.trigger_uuids = serial.trigger_uuids
        
    def get_serialized(self):
        return SerialSpline(self)
    
    def update_points(self):
        # TODO: This should take one point (the changed point) and only update its neighbors.
        points = []
        gpoints = []
        for guide in self.guides:
            gpoints.extend([guide.x, guide.y])
        self.gvl.resize(len(gpoints) / 2)
        self.gvl.vertices = gpoints
        colors = [.36, .56, .6] * (len(gpoints) / 2)
        colors[0 : 3] = [.6, .6, .36]
        colors[-3 :] = [.6, .36,.36]
        self.gvl.colors = colors
        d = 0
        while True:
            p = self.get_point(d)
            if not p:
                break
            points.extend([p.x, p.y])
            d += .05
        if points:
            color = [.6, .6, .6]
            if self.kind == 1:
                color = [.0, .0, .0]
            elif self.kind == 2:
                color = [.9, .3, .3]
            points.extend([gpoints[-2], gpoints[-1]])
            self.pvl.resize(len(points) / 2)
            self.pvl.vertices = points
            self.pvl.colors = color * (len(points) / 2)

    def add_guide(self, x, y):
        self.guides.append(Vec3(x, y))
        self.update_points()

    def remove_guide(self, guide):
        if guide in self.guides:
            self.guides.remove(guide)
            self.update_points()

    def move_guide(self, guide, x, y):
        if guide in self.guides:
            guide.x = x
            guide.y = y
            self.update_points()

    def on_trigger(self, trigger):
        colors = ["white", "black"]
        flock = Flock(self.scene, self, color=colors[self.kind])
        # TODO: add flock to world !!!
        self.scene.add_dynamic(flock)
        

    def get_point(self, distance):
        # use it like this
#    def update(self, dt):
#        if self.moving == True:
#            self.t += dt
#            self.p = self.spline.get_point(self.t)
#        if not self.p:
#            self.t = 0        
        if not self.guides:
            return
        guides = [self.guides[0]] + self.guides + [self.guides[-1]]
        distance += 1
        a = int(distance)
        b = distance - a
        if a + 3 > len(guides):
            return
        t1, t2, t3, t4 = guides[a-1 : a+3]
        q1 = b * ((2 - b) * b - 1) * t1
        q2 = (b * b * (3 * b - 5) + 2) * t2
        q3 = b * ((4 - 3 * b) * b + 1) * t3
        q4 = (b - 1) * b * b * t4
        return (q1 + q2 + q3 + q4) / 2.0

    def draw(self):
        if __debug__:
            glColor4f(1.0, 1.0, 1.0, 1.0)
            if self.guides:
                pyglet.gl.glPointSize(5)
                self.batch.draw()
        else:
            pass
            
cerealizer.register(Spline)

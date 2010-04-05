#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: entity.py 464 2009-09-02 22:53:12Z dr0iddr0id $'


from vectors import Vec3
import pyglet

#------------------------------------------------------------------------------

class Entity(object):

    def __init__(self, position=Vec3(0,0)):
#        self.rect = Rect(0,0,5,5)
        self.position = position
        self.bounding_radius = 5
        self.color = (.12, .96, .72)

    def draw(self):
        pyglet.gl.glPointSize(12)
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                             ('v2f', (self.position.x, self.position.y)),
                             ('c3f', self.color))    
        #raise NotImplementedError()
    
    def update(self, dt):
        raise NotImplementedError()

#------------------------------------------------------------------------------

class MovingEntity(Entity):

    def __init__(self, position=Vec3(0,0), velocity=Vec3(0,0), orientation=Vec3(1,0)):
        super(MovingEntity, self).__init__(position)
        self.velocity = velocity
        self.orientation = orientation

    def update(self, dt):
        #acceleration = self.force / self.mass
        #self.velocity += acceleration * dt
        self.position += self.velocity * dt
        # important if rect is used
        #self.rect.center = self.position.as_xy_tuple()

#------------------------------------------------------------------------------




#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: enemies.py 573 2009-09-07 19:58:59Z DLacewell $'

# maybe define a EnemyType class with params

import random

import pyglet
import cerealizer
from lib.entity import MovingEntity
from lib.vectors import Vec3


class Bullet(MovingEntity):

    def __init__(self, scene, position, velocity):
        super(Bullet, self).__init__(position, velocity)
        self.color = (1.0, 1.0, 0.0)
        self.scene = scene

    def update(self, dt):
        if self.position.get_distanceSQ(self.scene.campos + Vec3(400,300)) > 449*449:
            self.destroy()
        super(Bullet, self).update(dt)

    def destroy(self):
        try:
            self.scene.remove_dynamic(self)
            print "\n\n Destroyed bullet: %d \n\n" % len(self.scene.dynamic)
        except Exception, e:
            print "Error removing bullet, ", e.message
#------------------------------------------------------------------------------

class SerialEnemy(object):
    def __init__(self, enemy):
        self.position = enemy.position
        self.fire_rate = enemy.fire_rate
        self.orientation = enemy.orientation
cerealizer.register(SerialEnemy)

class Enemy(MovingEntity):

    def __init__(self, scene, fire_rate, position, orientation):
        super(Enemy, self).__init__(position, orientation=orientation)
        self.color = (0.2, 0.2, 0.5)
        self.scene = scene
        self.fire_rate = fire_rate
        pyglet.clock.schedule_once(self.fire, self.fire_rate)

    def get_serialized(self):
        return SerialEnemy(self)
        
    def update(self, dt):
        components = (0.2, 1.0)
        self.color = (random.choice(components), random.choice(components), random.choice(components))
    
    def hold(self):
        pyglet.clock.unschedule(self.fire)
        
    def fire_later(self):
        self.hold()
        pyglet.clock.schedule_once(self.fire, self.fire_rate)
        
    def fire(self, *args, **kwargs):
        self.hold()
        pyglet.clock.schedule_once(self.fire, self.fire_rate)
        if self.position.get_distanceSQ(self.scene.campos + Vec3(400,300)) < 449*449:
            b = Bullet(self.scene, self.position.clone(), self.orientation)
            self.scene.add_dynamic(b)
        

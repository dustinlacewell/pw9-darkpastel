#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: player.py 565 2009-09-06 12:30:41Z DLacewell $'


import entity
import pyglet

class Player(entity.MovingEntity): 

    def __init__(self):
        super(Player, self).__init__()
        self.color = "black"
        self.alive = 100
        self.movex = 0
        self.movey = 0
        self.speed = 300
        self.focus_speed = 300
        self.focused = False

    def update(self, dt):
        self.velocity.x = self.movex
        self.velocity.y = self.movey
        self.velocity.normalize()
        self.velocity *= self.speed
        super(Player, self).update(dt)

    def switchcolor(self):
        if self.color == "black":
            self.color = "white"
        else: 
            self.color = "black"

    def draw(self):
        blackcolors = [[.8, .8, .8], [.1, .1, .1]]
        for x in range(2):
            if self.color == "black":
                colors = blackcolors[x]
            else:
                r = list(blackcolors)
                r.reverse()
                colors = r[x]
            pyglet.gl.glPointSize(25 - (x * 6))
            pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                                 ('v2f', (self.position.x, self.position.y)),
                                 ('c3f', colors)) 
        #self.batch = batch or pyglet.graphics.Batch()
        #self.pvl = self.batch.add(1, pyglet.gl.GL_LINE_LOOP, None,
        #                         ('v2f', (0, 0)),
        #                         ('c3f', (0, 0, 0)))

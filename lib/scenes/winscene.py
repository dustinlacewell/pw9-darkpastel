#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: playlevelscene.py 564 2009-09-06 00:25:05Z dr0iddr0id $'

import collections
import cerealizer
import pyglet
from pyglet.gl import *
from pyglet.window.key import *
from pyglet import clock

from lib import scenes
from lib.spline import *

from lib.spacial import Space
from lib.player import Player
from lib.flock import Flock
from lib import collision
from lib.spline import Spline
from lib.enemies import Enemy
from lib.enemies import Bullet
from lib.obstacle import Polygon
from lib.obstacle import Trigger
from lib.util import GameLevel

CAMOFF = Vec3(400, 300)

#------------------------------------------------------------------------------
class WinScene(scenes.Scene):

    def __init__(self, app):
        super(WinScene, self).__init__(app)
        
        self.space = Space((400, 400))
        
        def f(a, b):
            if __debug__: pass#print "missing collision function tuple type (%s, %s)" % (a.__class__.__name__, b.__class__.__name__)
        
        #self.coll_funcs = coolections.defaultdict(lambda: lambda *args, **kwargs: None) # {(type1, type2): func}
        self.coll_funcs = collections.defaultdict(lambda: f) # {(type1, type2): func}

        self.coll_funcs[(Bullet, Player)] = self.coll_player_bullet
        #self.coll_funcs[(Player, Polygon)] = self.coll_player_obstacle
        self.coll_funcs[(Bullet, Polygon)] = self.coll_bullet_obstacle
        self.coll_funcs[(Flock, Polygon)] = self.coll_flock_obstacle
        self.coll_funcs[(Flock, Bullet)] = self.coll_flock_bullet
        self.coll_funcs[(Bullet, Flock)] = self.coll_bullet_flock
        self.coll_funcs[(Player, Flock)] = self.coll_player_flock
        self.coll_funcs[(Player, Trigger)] = self.coll_player_trigger

        self.splines = []
        self.flocks = []
        self.obstacles = []
        self.enemies = []
        self.triggers = []
        self.bullets = []
        
        self.dynamic = []
        self.static = []
        
        self.winlabel = None
        self.winmsg = "You win!"
        self.campos = Vec3(0.0, 0.0)
        self.last_lead = Vec3(0.0, 0.0)
        
        self.bg_image = pyglet.image.load("data/textures/background.png")
        self.bg_texture = pyglet.image.TileableTexture.create_for_image(self.bg_image)
        self.level_file = None #self.app.level_file
        
        self.load_level()
        
        self.cam_spline = None
        for spl in self.splines:
            if spl.kind == 2: # camera spline
                self.cam_spline = spl
        if self.cam_spline is None:
            print "wtf mate"
        self.t = 0
    
    def lookat(self, pos):
        self.campos = pos - CAMOFF 

    #-- collision function --#

    def coll_flock_obstacle(self, flock, obst):
        for boid in flock.boids:
            if obst.is_point_in(boid.position.x, boid.position.y):
                flock.boids.remove(boid)
    
    def coll_player_bullet(self,  bullet, player):
        player.alive -= 10
        bullet.destroy()
        if __debug__: print 'collision player - bullet'
        pass    

    def coll_player_obstacle(self, player, obst):
        if obst.is_point_in(player.position.x, player.position.y):
            d = obst.position - player.position
            minval = 0
            for vertex in obst.vertices:
                value = d.dot(vertex)
                if value < min:
                    vert = vertex
                    minval = value
            d.normalize()
            player.position += vertex.project_onto(d) * 0.1
            #if __debug__: print player.velocity, player.position, vertex.project_onto(d)
            #if __debug__: print 'collision, player - obstacle!'
        
    def coll_bullet_obstacle(self, bullet, obst):
        if obst.is_point_in(bullet.position.x, bullet.position.y):
            bullet.destroy()
            #if __debug__: print 'collision, bullet - obstacle!'

    def coll_bullet_flock(self, bul, flock):
        self.coll_flock_bullet(flock, bul)

    def coll_flock_bullet(self, flock, bullet):
        if flock.boids:
            boid = min([((boid.position - bullet.position).lengthSQ, boid) for boid in flock.boids])
            if boid[0] < 20:
                flock.boids.remove(boid[1])
                bullet.destroy()
                if __debug__: print 'collision, flcok - bullet!'

    def coll_player_flock(self, player, flock):
        if player.color != flock.color:
            player.alive -= 1
            if __debug__: print 'collision, player - flock!'
        
    def coll_player_trigger(self, player, trigger):
        trigger.fire()

    def have_level(self, level_number):
        pass

    def load_level(self):
        self.level_file = "data/WinLevel.lvl"
        level = None
        fobj = open(self.level_file, "rb")
        level = cerealizer.load(fobj)

        if level:
            self.splines = [Spline(self, serial=s) for s in level.splines]
            self.triggers = [Trigger(0, 0, serial=t) for t in level.triggers]
            self.obstacles = [Polygon(self, serial=o) for o in level.obstacles]
            self.enemies = [Enemy(self, s.fire_rate, s.position, s.orientation) for s in level.enemies]
            # connect triggers
            for spl in self.splines:
                for trigger_uuid in spl.trigger_uuids:
                    for trigger in self.triggers:
                        if trigger.uuid == trigger_uuid:
                            trigger += spl.on_trigger
                            
            self.static.extend( self.triggers + self.obstacles + self.enemies )
            self.space.add(self.static)

    #-- state funcs --#
            
    def on_scene_enter(self):
        #glEnable(GL_POINT_SMOOTH)
        #glEnable(GL_TEXTURE_2D)
        self.player = Player()
        self.players = [self.player]
        self.dynamic.append(self.player)
        self.last_lead = self.player.position = self.campos = self.cam_spline.get_point(0)
        clock.schedule(self.update)
            
        
    def on_scene_leave(self):
        #glDisable(GL_POINT_SMOOTH)
        #glDisable(GL_TEXTURE_2D)
        clock.unschedule(self.update)
        
    def add_dynamic(self, bullet):
        self.dynamic.append(bullet)
    
    def remove_dynamic(self, bullet):
        try:
            self.dynamic.remove(bullet)
        except:
            pass
 

    def update(self, dt):
        # update spline and get position
        self.t += dt * 0.45
        
        self.winlabel = pyglet.text.Label(self.winmsg,
                            font_name='System',
                            font_size=42,
                            x=self.app.width / 2, y=self.app.height / 2,
                            anchor_x='center', anchor_y='center',
                            color=(86,10,10, 255))
        
        lead_point = self.cam_spline.get_point(self.t)
        if lead_point:
            camdelta = lead_point - self.last_lead
            self.last_lead = lead_point
            self.lookat(lead_point)
            self.player.position += camdelta
        else:
            pass  
    
        dynamics = self.dynamic #[dyn for dyn in self.dynamic if dyn.position.get_distanceSQ(self.campos) < 800*800]
        for dynamic in dynamics:
            dynamic.update(dt)
        # collision
        for item, bhits in self.space.add(dynamics):
            if bhits:
                for bitem in bhits:
                    r = item.bounding_radius + bitem.bounding_radius
                    if r * r > item.position.get_distanceSQ(bitem.position):
                        self.coll_funcs[item.__class__, bitem.__class__](item, bitem)
        
        self.space.remove(dynamics)
        if self.player.alive < 0:
            pass

    def on_draw(self):
        self.app.clear()
        glLoadIdentity()
        glColor4f(1.0, 1.0, 1.0, 1.0)
        
        # Background
        self.bg_texture.blit_tiled(0, 0, 0, 800, 600)
        # Camera translation
        glTranslatef(-self.campos.x, -self.campos.y, 0.0)
        
        for dyn in self.dynamic:
            dyn.draw()
        self.player.draw()
        for stat in self.static:
            stat.draw()
        
        glTranslatef(self.campos.x, self.campos.y, 0.0)
        if self.winlabel:
            self.winlabel.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass
    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        
        if pyglet.window.mouse.MIDDLE == button and __debug__:
            self.campos += Vec3(dx, dy)

    def on_key_press(self, symbol, mod):
        if symbol == UP:
            self.player.movey += 1
        elif symbol == DOWN:
            self.player.movey -= 1
        elif symbol == RIGHT:
            self.player.movex += 1
        elif symbol == LEFT:
            self.player.movex -= 1
        elif symbol == SPACE:
            self.player.switchcolor()

    def on_key_release(self, symbol, mod):
        if symbol == UP:
            self.player.movey -= 1
        elif symbol == DOWN:
            self.player.movey += 1
        elif symbol == RIGHT:
            self.player.movex -= 1
        elif symbol == LEFT:
            self.player.movex += 1

    def on_scene_leave(self):
        clock.unschedule(self.update)

scene_class = WinScene

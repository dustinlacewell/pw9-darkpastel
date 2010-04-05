#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: playgroundscene.py 558 2009-09-05 22:13:37Z DLacewell $'

import pyglet
from pyglet.gl import *
from pyglet.window.key import *
from pyglet import clock

from lib import scenes
from lib import enemies
from lib import flock
from lib.spline import *




from lib.player import Player
from lib.flock import Flock
from lib import collision
from lib.spline import Spline
from lib.enemies import Enemy
from lib.obstacle import Polygon

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
    
class PlayerBulletsCollisionStrategy(collision.ICollisionStrategy):

    def __init__(self, scene):
        self.scene = scene
        
    def check_broad(self, name1, name2, coll_groups):
        return collision.brute_force_radius(coll_groups[name1], coll_groups[name2])

    def check_narrow(self, pairs_list, coll_funcs):
        for player, bullet in pairs_list:
            player.alive -= 10
            bullet.destroy()
            print 'collision player - bullet'
            pass

#------------------------------------------------------------------------------
    
class PlayerObstaclesCollisionStrategy(collision.ICollisionStrategy):

    def __init__(self, scene):
        self.scene = scene
        
    def check_broad(self, name1, name2, coll_groups):
        return collision.brute_force_radius(coll_groups[name1], coll_groups[name2])

    def check_narrow(self, pairs_list, coll_funcs):
        for player, flock in pairs_list:
            print 'collision, player - obstacle!'

#------------------------------------------------------------------------------
    
class BulletsObstaclesCollisionStrategy(collision.ICollisionStrategy):

    def __init__(self, scene):
        self.scene = scene
        
    def check_broad(self, name1, name2, coll_groups):
        return collision.brute_force_radius(coll_groups[name1], coll_groups[name2])

    def check_narrow(self, pairs_list, coll_funcs):
        for bullet, obstacle in pairs_list:
            if obstacle.is_point_in(bullet.position.x, bullet.position.y):
                bullet.destroy()
                print 'collision, bullet - obstacle!'

#------------------------------------------------------------------------------
    
class FlockBulletsCollisionStrategy(collision.ICollisionStrategy):

    def __init__(self, scene):
        self.scene = scene
        
    def check_broad(self, name1, name2, coll_groups):
        return collision.brute_force_radius(coll_groups[name1], coll_groups[name2])

    def check_narrow(self, pairs_list, coll_funcs):
        for flock, bullet in pairs_list:
            if flock.boids:
                boid = min([((boid.position - bullet.position).lengthSQ, boid) for boid in flock.boids])
                if boid[0] < 500:
                    flock.boids.remove(boid[1])
                    bullet.destroy()
                    print 'collision, flcok - bullet!'

#------------------------------------------------------------------------------
class PlayerFlockCollisionStrategy(collision.ICollisionStrategy):
    # custom collision strategy for ball wall collision
    # collision at the wall edges is not perfect
    def __init__(self, scene):
        self.scene = scene

    def check_broad(self, name1, name2, coll_groups):
        return collision.brute_force_radius(coll_groups[name1], coll_groups[name2])

    def check_narrow(self, pairs_list, coll_funcs):
        # check for collision
        for player, flock in pairs_list:
            if player.color != flock.color:
                player.alive -= 1
                print 'collision, player - flock!'
                # collision response
                #coll_funcs[(ball.__class__, wall.__class__)](ball, wall, ball.bounding_radius - n_len)
#------------------------------------------------------------------------------
class PlayGroundScene(scenes.Scene):

    def __init__(self, app):
        super(PlayGroundScene, self).__init__(app)
        spline = Spline(self)
        spline.add_guide(100, 100)
        spline.add_guide(100, 200)
        spline.add_guide(100, 250)
        spline.add_guide(300, 50)
        spline.add_guide(400, 150)
        spline.add_guide(400, 400)
        spline.add_guide(200, 300)
        spline.add_guide(100, 100)
        self.flocks = [Flock(spline, 30, position=Vec3(100,100), color="black")]
        spline = Spline(self)
        spline.add_guide(750, 500)
        spline.add_guide(100, 480)
        spline.add_guide(150, 50)
        spline.add_guide(200, 100)
        spline.add_guide(500, 25)
        spline.add_guide(700, 300)
        spline.add_guide(750, 500)
        
        self.flocks.append(Flock(spline, 30, position=Vec3(200,200), action="reset"))
        self.obstacles = []
        self.player = None
        self.enemies = []
        self.bullets = []
        self.coll_detector = None

    def add_dynamic(self, entity):
        if isinstance(entity, enemies.Bullet):
            self.bullets.append(entity)
        elif isinstance(entity, flock.Flock):
            self.flocks.append(entity)
        else:
            print 'UNKNOWN  entity type to add', entity.__class__.__name__

    def remove_dynamic(self, entity):
        try:
            if isinstance(entity, enemies.Bullet):
                self.bullets.remove(entity)
            elif isinstance(entity, flock.Flock):
                self.flocks.remove(entity)
            else:
                print 'UNKNOWN entity type to remove', entity.__class__.__name__
        except:
            pass

        
    def on_scene_enter(self):
        clock.schedule(self.update)
        
        self.player = Player()
        self.players = [self.player]
        self.generate_level()
        
        # set up collision detection
        self.coll_detector = collision.CollisionDetector()
        
        # collisions between:
        # flock-player, player-bullets, player-objstacles, bulltets-obstacles, bullets-flock
        #self.coll_detector.register_once(self, group_name1, group_name2, group1, group2, coll_strategy, type_tuple, func):
        self.coll_detector.register_group('player', self.players)
        self.coll_detector.register_group('flocks', self.flocks)
        self.coll_detector.register_group('obstacles', self.obstacles)
        self.coll_detector.register_group('enemies', self.enemies)
        self.coll_detector.register_group('bullets', self.bullets)
        self.coll_detector.register_pair('player', 'flocks', PlayerFlockCollisionStrategy(self))
        self.coll_detector.register_pair('player', 'bullets', PlayerBulletsCollisionStrategy(self))
        self.coll_detector.register_pair('player', 'obstacles', PlayerObstaclesCollisionStrategy(self))
        self.coll_detector.register_pair('bullets', 'obstacles', BulletsObstaclesCollisionStrategy(self))
        self.coll_detector.register_pair('flocks', 'bullets', FlockBulletsCollisionStrategy(self))
        
        #self.coll_detector.register_once('player', 'flocks', self.players, self.flocks, PlayerFlockCollisionStrategy(self), tuple(), None):
        
        # enemy
        #scene, fire_rate, position, orientation)
        self.enemies.append( Enemy(self, 1, Vec3(300, 10), Vec3(0, 1) * 100.0) )
        self.enemies.append( Enemy(self, 0.1, Vec3(10, 200), Vec3(1, -0.1) * 300.0) )
        self.enemies.append( Enemy(self, 1, Vec3(500, 10), Vec3(0, 1) * 200) )
        
        p = Polygon()
        p.add_vertex(400, 400)
        p.add_vertex(550, 400)
        p.add_vertex(550, 420)
        p.add_vertex(400, 450)
        self.obstacles.append(p)

    def generate_level(self):
        # TODO: implement level generation here
        pass
        
    def update(self, dt):
        for flock in self.flocks:
            flock.update(dt)
        for obst in self.obstacles:
            obst.update(dt)
        for enemy in self.enemies:
            enemy.update(dt)
        for bullet in self.bullets:
            bullet.update(dt)
        self.player.update(dt)
        
        self.coll_detector.check()
        
        #print self.player.alive
        if self.player.alive < 0:
            print 'dead!'
            pass

    def on_draw(self):
        
        self.app.clear()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        for flock in self.flocks:
            flock.draw()
        glColor4f(1,1,1,1)
        for obst in self.obstacles:
            obst.draw()
        for enemy in self.enemies:
            enemy.draw()
        for bullet in self.bullets:
            bullet.draw()
        self.player.draw()

        self.app.draw_fps()
        
    def on_mouse_press(self, x, y, button, modifiers):
        pass

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

scene_class = PlayGroundScene

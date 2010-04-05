#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
TODO: docstring
"""

__version__ = '$Id: flock.py 569 2009-09-07 03:24:42Z DLacewell $'

import random

import pyglet

from lib.entity import MovingEntity
from lib.vectors import Vec3

class Boid(MovingEntity):
    def __init__(self, flock, *args, **kwargs):
        self.flock = flock
        super(Boid, self).__init__(*args, **kwargs)
        self.velocity = Vec3(0,0)
        
    def draw(self):
        pyglet.gl.glPointSize(12)
        rot = self.velocity.angle - 45.0
        pyglet.gl.glTranslatef(self.position.x, self.position.y, 0.0)
        pyglet.gl.glRotatef(rot, 0, 0, 1)
        pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                             ('v2f', (-2, 0, 0, -10, 2, 0, 0, 10)),
                             ('c3f', self.color*4)) 
        #self.batch = batch or pyglet.graphics.Batch()
        #self.pvl = self.batch.add(1, pyglet.gl.GL_LINE_LOOP, None,
        #                         ('v2f', (0, 0)),
        #                         ('c3f', (0, 0, 0)))
        pyglet.gl.glRotatef(-rot, 0, 0, 1)
        pyglet.gl.glTranslatef(-self.position.x, -self.position.y, 0.0)
        
    def update(self, dt):
        # rules
        v1 = self.adjust_towards_flock() * self.flock.TIGHTNESS_FACTOR
        v2 = self.avoid_others() * self.flock.SPACING_FACTOR
        v3 = self.match_flock_speed() * self.flock.SPEED_FACTOR
        # move towards spline position
        v4 = self.flock.position - self.position
        # apply all movements
        self.velocity = self.velocity  + v1 + v3 + v2 + v4 * 2.5
        # dampening movement
        self.velocity *= 0.075
        # insert some randomness
        #self.velocity.rotate(random.randint(0, 360), Vec3(0,0,1))
        v = self.velocity
        a = self.get_angle
        self.velocity.rotate(a(v, v1) + a(v, v2) + a(v, v3) + a(v, v4), Vec3(0,0,1))
        # move
        super(Boid, self).update(dt)
    
    def get_angle(self, v, v2): # -> angle, sign
        sign = 1
        if v.cross(v2).z < 0:
            sign = -1
        return v.get_angle_between(v2) * sign
    
    def adjust_towards_flock(self):
        # Rule 1: Boids try to fly towards the centre of mass of neighbouring boids. 
#        pos = sum([boid.position for boid in self.flock.boids], Vec3(0,0))
        # remove myself
#        pos -= self.position
#        pos /= (len(self.flock.boids) - 1)
        # move
#        return pos - self.position
        # just cheating for speed
        return (self.flock.position - self.position) * 0.5
    
    def avoid_others(self):
        # Rule 2: Boids try to keep a small distance away from other objects (including other boids). 
        c = Vec3(0, 0)
        distSQ = 20 * 20
        for boid in self.flock.boids:
            d = boid.position - self.position
            if d.lengthSQ < distSQ:
                c -= d
        return c
    
    def match_flock_speed(self):
        # Rule 3: Boids try to match velocity with near boids. 
        #vel = sum([boid.velocity for boid in self.flock.boids], Vec3(0,0))
        # this is faster than the line above
        vel = Vec3(0,0)
        for boid in self.flock.boids:
            vel += boid.velocity
        # remove itself
        vel -= self.velocity
        # average
        vel /= (len(self.flock.boids) - 1)
        # weight the result
        return vel - self.velocity

#------------------------------------------------------------------------------
import random
from math import sin, cos, tan

class Boid2(object):

    def __init__(self, flock, pos, batch, max_force=700.0, max_speed=260.0, min_force=500.0, min_speed=0.0, *args, **kwargs):
        # pos, vel, orient are from  MovingEntity
        self.position = pos.clone()
        self.velocity = Vec3(random.randint(-10, 10), random.randint(-10, 10), 0)
        self.bounding_radius = 100.0
        self.flock = flock
        self._max_force = max_force
        self._max_speed = max_speed + random.randint(-50, 50)
        self._min_force = min_force
        self._min_speed = min_speed
        self._distance = 10.0
        self._max_force_sq = max_force * max_force
        self._max_speed_sq = max_speed * max_speed
        self._min_force_sq = min_force * min_force
        self._min_speed_sq = min_speed * min_speed
#        self._old_position = Vec3(0, 0)
#        self._old_position.values = self.position
        self.acceleration = Vec3(0,0)
        self._steering_force = Vec3(0,0)
        self.bounds_radius = 50000
        self.bounds_center = Vec3(400,300)
        self._last_seeking = Vec3(400,300)
        self.radius = 10
        self._wander_theta = 180.0
        self._wander_radius = 35.0
        self._wander_distance = 60.0
        self._wander_step = 0.25
        self._max_angle = 0.0
        self.batch = batch
        self.sprite = pyglet.sprite.Sprite(self.flock.whitebird_img, batch = self.batch)
#        self._look_at_target = True
        
    def _set_max_force(self, value):
        self._max_force = max(0, value)
        self._max_force_sq = self._max_force ** 2
    max_force = property(lambda self: self._max_force, _set_max_force)
    
    def _set_max_speed(self, value):
        self._max_speed = max(0, value)
        self._max_speed_sq = self._max_speed ** 2
    max_speed = property(lambda self: self._max_speed, _set_max_speed)
    
    def _set_min_force(self, value):
        self._min_force = max(0, value)
        self._min_force_sq = self._min_force ** 2
    min_force = property(lambda self: self._min_force, _set_min_force)
    
    def _set_min_speed(self, value):
        self._min_speed = max(0, value)
        self._min_speed_sq = self._min_speed ** 2
    min_speed = property(lambda self: self._min_speed, _set_min_speed)

    def _set_wander_step(self, value):
        self._wander_step = value
    wander_step = property(lambda self: self._wander_step, _set_wander_step)    

    def _set_wander_distance(self, value):
        self._wander_distance = value
    wander_distance = property(lambda self: self._wander_distance, _set_wander_distance)    
    
    def _set_wander_radius(self, value):
        self._wander_radius = value
    wander_radius = property(lambda self: self._wander_radius, _set_wander_radius)    
    
    def _set_look_at_target(self, value):
        self._look_at_target = value
    look_at_target = property(lambda self: self._look_at_target, _set_look_at_target)    
    
    def update(self, dt):
#        self._old_position.values = self.position
        angle = abs(self.velocity.get_angle_between(self._last_seeking))
        if angle > self._max_angle: self._max_angle = angle
        anglefactor = 1.0 - (angle / 300.0)
        stopping_force = self._last_seeking - self.position
        dist = stopping_force.normalize()
        if dist > 0.0001:
            if dist < 50.0:
                self.acceleration.length *=  (max(dist, 10) / 100.0)
        self.acceleration *= anglefactor
        
        self.velocity += self.acceleration * dt
        if self.velocity.lengthSQ > self._max_speed_sq:
            self.velocity.length = self._max_speed
        elif self.velocity.lengthSQ < self._min_speed_sq:
            self.velocity.length = self._min_speed
           
            
        self.position += self.velocity * dt
        
        self.acceleration.x = 0
        self.acceleration.y = 0
        self.acceleration.z = 0
        
        
        
        dist = self.position.get_distance(self.bounds_center)
        if dist > self.bounds_radius + self.radius:
            self.position -= self.bounds_center
            self.position.length = self.bounds_radius + self.radius
            self.velocity *= -1
            self.position += self.velocity * dt
            self.position += self.bounds_center
        self.update_sprite()
        
    def brake(self, braking_force=0.01):
        self.velocity *= 1 - braking_force
        
    def seek(self, target, multiplier=1.0):
        self._last_seeking = target
        self._steering_force.values = self._steer(target)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force
    
    def arrive(self, target, ease_dist=100.0, multiplier=1.0):
        self._last_seeking = target
        self._steering_force.values = self._steer(target, True, ease_dist)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force
        
    def flee(self, target, panic_dist=100, multiplier=1.0):
        dist = self.position.get_distance(target)
        if dist > panic_dist:
            return
            
        self._steering_force.values = self._steer(target, True, -dist)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self._steering_force *= -1.0
        self.acceleration += self._steering_force
    
    def do_wander(self, multiplier=1.0):
        self._wander_theta += (random.random() * self._wander_step)
        if random.random() < 0.5:
            self._wander_theta *= -1
            
        pos = self.velocity.clone()
        
        pos.length = self._wander_distance
        pos += self.position
        
        offset = Vec3(0,0)
        offset.x = self._wander_radius * cos(self._wander_theta)
        offset.y = self._wander_radius * sin(self._wander_theta)
        offset.z = self._wander_radius * tan(self._wander_theta)
        
        self._steering_force = self._steer(pos + offset)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force
        
    def do_flock(self, boids, sep_weight=20.5, align_weight=0.2, cohesion_weight=0.2, \
                                sep_dist=300.0, align_dist=200.0, cohesion_dist=200.0):
        self.separate(boids, sep_dist, sep_weight)
        #self.align(boids, align_dist, align_weight)
        #self.cohesion(boids, cohesion_dist, cohesion_weight)
                
    def separate(self, boids, sep_dist=50.0, multiplier=1.0):
        self._steering_force = self._get_separation(boids, sep_dist)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force

    def align(self, boids, neighbor_dist=40.0, multiplier=1.0):
        self._steering_force = self._get_alignment(boids, neighbor_dist)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force

    def cohesion(self, boids, neighbor_dist=10.0, multiplier=1.0):
        self._steering_force = self._get_cohesion(boids, neighbor_dist)
        if multiplier != 1.0:
            self._steering_force *= multiplier
        self.acceleration += self._steering_force
        
    def reset(self):
        self.velocity = Vec3(0,0)
        self.position = Vec3(0,0)
        self._old_position = Vec3(0,0)
        self.acceleration = Vec3(0,0)
        self._steering_force = Vec3(0,0)
        
    def _steer(self, target, ease=False, ease_dist=100.0):
        _steering_force = target - self.position
        if _steering_force.angle < 5:
            _steering_force.rotate(15, Vec3(0, 0, 1.0))
        #angle = self.velocity.get_angle_between(target)
        #if angle > self._max_angle: self._max_angle = angle
        #print self._max_angle
        #print angle, _steering_force.angle
        #anglefactor = 1.0 - (angle / 180.0)
        dist = _steering_force.normalize()
        if dist > 0.0001:
            if dist < ease_dist and ease:
                _steering_force.length *=  self._max_speed * (dist  / ease_dist)
               
            else:
                _steering_force.length *= self._max_speed
                
            #_steering_force.normalize()
            #_steering_force.length *= anglefactor * self._max_speed * (dist  / ease_dist)
            
            if _steering_force.lengthSQ > self._max_force_sq:
                _steering_force.length = self._max_force
            elif _steering_force.lengthSQ < self._min_force_sq:
                _steering_force.length = self._min_force
        return _steering_force
        
    def _get_separation(self, boids, sep=25.0):
        force = Vec3(0,0)
        count = 0
        for boid in boids:
            dist = self.position.get_distance(boid.position)
            if dist > 0 and dist < sep:
                diff = self.position - boid.position
                diff.normalize()
                diff /= dist
                
                force += diff
                count += 1
        if count > 0:
            force /= count
            
        return force
        
    def _get_alignment(self, boids, neighbor_dist=50.0):
        count = 0
        force = Vec3(0,0)
        for boid in boids:
            dist = self.position.get_distance(boid.position)
            if dist > 0 and dist < neighbor_dist:
                force += boid.velocity
                count += 1
        if count:
            force /= count
            if force.lengthSQ > self._max_force:
                force.length = self._max_force
                
        return force
        
    def _get_cohesion(self, boids, neighbor_dist=50.0):
        force = Vec3(0,0)
        count = 0
        for boid in boids:
            dist = self.position.get_distance(boid.position)
            if dist > 0 and dist < neighbor_dist:
                force += boid.position
                count += 1
        if count:
            force /= count
            force = self._steer(force)
            
        return force
        
    def update_sprite(self):
        rotation = self.velocity.angle
        self.sprite.position = (self.position.x, self.position.y)
        self.sprite.rotation = -rotation + 90

    def draw(self):
        return
        blackcolors = [[.8, .8, .8], [.1, .1, .1]]
        
        rot = self.velocity.angle - 90.0
        pyglet.gl.glTranslatef(self.position.x, self.position.y, 0.0)
        pyglet.gl.glRotatef(rot, 0, 0, 1)
        for x in range(2):
            if self.color == "black":
                colors = blackcolors[x]
            else:
                r = list(blackcolors)
                r.reverse()
                colors = r[x]
            pyglet.gl.glLineWidth(5 - (x * 1))
            pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                                 ('v2f', (-15, 0, 0, 15, 15, 0, 0, 5)),
                                 ('c3f', colors*4)) 
        #self.batch = batch or pyglet.graphics.Batch()
        #self.pvl = self.batch.add(1, pyglet.gl.GL_LINE_LOOP, None,
        #                         ('v2f', (0, 0)),
        #                         ('c3f', (0, 0, 0)))
        pyglet.gl.glRotatef(-rot, 0, 0, 1)
        pyglet.gl.glTranslatef(-self.position.x, -self.position.y, 0.0)

            
            
#------------------------------------------------------------------------------
class Flock(MovingEntity):
    TIGHTNESS_FACTOR = 0.001
    SPACING_FACTOR = 3.5
    SPEED_FACTOR = 0.125
    def __init__(self, scene, spline, num_boids=25, action="loop", color="white", *args, **kwargs):
        super(Flock, self).__init__(*args, **kwargs)
        self.scene = scene
        self.boids = []
        self.action = action

        self.batch = pyglet.graphics.Batch()
        self.whitebird_img = pyglet.image.load("data/textures/%sbird.png" % color)
        self.onscreen = False

        for i in range(num_boids):
            xoff = 2 * random.random() - 0.5 #random.randint(-num_boids, num_boids) * 10 * 0
            yoff = 2 * random.random() - 0.5 #random.randint(-num_boids, num_boids) * 10 * 0
            self.boids.append(Boid2(self, Vec3(spline.guides[0].x+xoff, spline.guides[0].y+yoff), batch=self.batch))
            self.boids[-1].velocity.x = xoff * 10
            self.boids[-1].velocity.y = yoff * 10
            self.boids[-1].color = color

        # spline
        self.spline = spline
        self.t = 0
        self.lead_point = None
        self.color = color
        self.bounding_radius = 200
        
    
    def draw(self):
        #super(Flock, self).draw()
        self.spline.draw()
        if self.lead_point:
            self.position = self.lead_point
        self.batch.draw()
        #for boid in self.boids:
        #    boid.draw()

    def reset(self, time=0):
        self.t = time
        lead_point = self.spline.get_point(self.t)
        num_boids = len(self.boids)
        for b in self.boids:
                xoff = 2 * random.random() - 0.5 
                yoff = 2 * random.random() - 0.5
                b.position=Vec3(lead_point.x+xoff, lead_point.y+yoff)
                b.velocity.x = xoff * 10
                b.velocity.y = yoff * 10    

    def update(self, dt):
        # update spline and get position
        self.t += dt * 0.45
        self.lead_point = self.spline.get_point(self.t)
        if not self.lead_point:
            if self.action == "loop":
                self.t = 0
            elif self.action == "reset":
                self.reset()
        onscreen = False
        if self.lead_point:
            onscreen = self.lead_point.get_distanceSQ(self.scene.campos + Vec3(400,300)) < 420*420
            if not self.onscreen and onscreen:
                self.reset(time=self.t)
                self.onscreen = onscreen
        if onscreen:
        # update boids
            for boid in self.boids:
                if not self.scene.player.color ==  self.color:
                    if self.lead_point:
                        boid.seek(self.lead_point, multiplier=10.0)
                    #boid.do_flock(self.boids)
                    boid.do_wander(multiplier=5)
                    boid.flee(self.scene.player.position, panic_dist=100, multiplier=20.0)
                else:
                    if self.lead_point:
                        boid.seek(self.lead_point, multiplier=10.0)
                    #boid.do_flock(self.boids)
                    boid.do_wander(multiplier=5)
                    boid.flee(self.scene.player.position, panic_dist=100, multiplier=4.0)
                    
            for boid in self.boids:
                boid.update(dt)
    #        print self.boids[0].velocity.angle
    #        print '?------------?'
            
                
    def update_old(self, dt):
        # update spline and get position
        self.t += dt
        self.lead_point = self.spline.get_point(self.t)
        if not self.lead_point:
            if self.action == "loop":
                self.t = 0
            elif self.action == "reset":
                self.reset()
        # update buids
        radiusSQ = 0
        if len(self.boids) > 1:
            for boid in self.boids:
                boid.update(dt)
    #            d = (boid.position - self.position).lengthSQ
    #            if d > radiusSQ:
    #                radiusSQ = d
    #        self.bounding_radius = radiusSQ ** 0.5
            self.bounding_radius = max([(boid.position - self.position).lengthSQ for boid in self.boids]) ** 0.5

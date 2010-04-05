import os

import pyglet
from pyglet.gl import *

import cerealizer

import lib
from lib import obstacle
from lib import enemies
from lib import spline
from lib.vectors import Vec3

CAMOFF = Vec3(400, 300)

#------------------------------------------------------------------------------

class EditorState(object):
    def __init__(self, editor):
        self.editor = editor
    def enter(self):
        pass
    def exit(self):
        pass
    def update(self, dt):
        pass
    def draw(self):
        pass
    def mouse_press(self, x, y, button, modifiers):
        pass
    def mouse_release(self, x, y, button, modifiers):
        pass
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        pass
    def key_press(self, key, modifiers):
        pass
    def key_release(self, key, modifiers):
        pass
    def lookat(self, pos):
        return self.editor.lookat(pos) 

#------------------------------------------------------------------------------

class EnemyEditState(EditorState):
    
    ENEMYGRABDIST = 30.0
    statusinfo = "Editing an enemy."
    
    def __init__(self, editor, enemy=None):
        self.editor = editor
        self.enemy = enemy
        
        
    def enter(self):
        if self.enemy:
            self.enemy = None
        
    def draw(self):
        if self.enemy:
            pos = self.enemy.position
            off = pos - self.enemy.orientation
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2f', (pos.x, pos.y, off.x, off.y)),
                ('c3f', (1.0, 1.0, 1.0, 0.0, 0.0, 0.0)))
                
    def update(self, dt):
        if self.enemy: 
            if __debug__: print self.enemy.fire_rate
        for bullet in self.editor.bullets:
            bullet.update(dt)
             
    def mouse_press(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if not self.enemy:
                closest = self._get_closest(x, y)
                if closest:
                    self.enemy = closest
                    self.enemy.fire()
            else:
                self.enemy.fire()
            
            
    def _get_closest(self, x, y):
        closest = None
        dist = self.ENEMYGRABDIST
        d = dist + 1
        for enemy in self.editor.enemies:
            try:
                d = Vec3(x, y).get_distance(enemy.position)
            except ValueError, e:
                if __debug__: print e.message
                if __debug__: print x, y, enemy.position.x, enemy.position.y
                continue
            if d < dist:
                dist = d
                closest = enemy
        return closest
                
    def mouse_release(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.enemy:
                self.enemy.hold()              
                if not modifiers:
                    self.enemy.position = Vec3(x, y)
                self.enemy = None
        elif pyglet.window.mouse.RIGHT == button:
            enemy = self._get_closest(x, y)
            if enemy:
                self.editor.enemies.remove(enemy)
            self.enemy = None
                
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.enemy:
                if modifiers & pyglet.window.key.MOD_ALT:
                    self.enemy.hold()    
                    self.enemy.fire_rate  = max(0.001, self.enemy.fire_rate + dy * 0.03)
                    self.enemy.fire_rate = min(1.5, self.enemy.fire_rate)
                    self.enemy.fire_later()
                elif modifiers & pyglet.window.key.MOD_CTRL:
                    self.enemy.orientation = self.enemy.position - Vec3(x, y)
                else:
                    self.enemy.position = Vec3(x, y)
                    
    def key_press(self, key, modifiers):
        if pyglet.window.key.ENTER == key:
            self.editor.set_statusline("Left enemy-mode.", temp=True)
            self.editor.pop_state()
        elif pyglet.window.key.N == key:
            self.editor.enemies.append(enemies.Enemy(self.editor, 1.0, self.editor.lastmousepos, Vec3(0, 0)))

#------------------------------------------------------------------------------

class ObstacleEditState(EditorState):
    
    POINTGRABDIST = 10.0
    statusinfo = "Editing an obstacle."
    
    def __init__(self, editor, obstacle=None):
        self.editor = editor
        self.obstacle = obstacle
        
    def enter(self):
        if self.obstacle:
            self.lookat(self.obstacle.vertices[0])
        else:
            self.obstacle = obstacle.Polygon(self.editor, texture=self.editor.get_current_texture())
        self.point = None
        
    def draw(self):
        self.obstacle.draw_open()
        if self.point:
            pyglet.gl.glPointSize(7)
            pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                                 ('v2f', (self.point.x, self.point.y)),
                                 ('c3f', (.6, .48, .36)))
        
    def mouse_press(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if not self.point:
                closest = self._get_closest(x, y)
                if closest:
                    self.point = closest
                else:
                    valid = self.obstacle.add_vertex(x, y)
                    self.point = self.obstacle.vertices[-1]
                    if not valid:
                        self.editor.set_statusline("polygon is invalid!", temp=True)
        elif pyglet.window.mouse.RIGHT == button:
            closest = self._get_closest(x,y)
            if closest:
                self.obstacle.remove_vertex(closest)

    def _get_closest(self, x, y):
        """ returns either a Vec3 or None"""
        closest = None
        dist = self.POINTGRABDIST
        d = dist + 1
        for point in self.obstacle.vertices:
            try:
                d = Vec3(x, y).get_distance(Vec3(point.x, point.y))
            except ValueError, e:
                if __debug__: print e.message
                if __debug__: print x, y, point.x, point.y
                continue
            if d < dist:
                dist = d
                closest = point
        return closest
        
    def mouse_release(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.point:
                self.obstacle.move_vertex(self.point, x, y)
                self.point = None
                if not self.obstacle.check_vertex_valid():
                    self.editor.set_statusline("Invalid!!", temp=True)
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.point:
                valid = self.obstacle.move_vertex(self.point, x, y)
                if not valid:
                    self.editor.set_statusline("Invalid!!", temp=True)
                    
                    
    def key_press(self, key, modifiers):
        if pyglet.window.key.ENTER == key:
            if len(self.obstacle.vertices) < 3:
                self.editor.set_statusline("Incomplete obstacle not saved. Left obstacle-mode", temp=True)
            elif not self.obstacle.check_vertex_valid():
                self.editor.set_statusline("Invalid (not convex) obstacle not saved. Left obstacle-mode", temp=True)
            elif self.obstacle not in self.editor.obstacles:
                self.editor.obstacles.append(self.obstacle)
                self.editor.set_statusline("Saved obstacle. Left obstacle-mode.", temp=True)
            self.editor.pop_state()
        elif pyglet.window.key.C == key:
            self.obstacle.set_texture(self.editor.get_next_texture())
        elif pyglet.window.key.TAB == key:
            if self.obstacle not in self.editor.obstacles:
                if len(self.obstacle.vertices) < 3 or not self.obstacle.check_vertex_valid():
                    self.editor.set_statusline("Incomplete or invalid obstacle not saved. Viewing #0", temp=True)
                else:
                    self.editor.obstacles.append(self.obstacle)
                idx = 0
            else:
                idx = self.editor.obstacles.index(self.obstacle) - 1
                self.editor.set_statusline("Viewing obstacle #%d" % idx, temp=True)
            self.editor.pop_state()
            self.editor.push_state(ObstacleEditState(self.editor, obstacle=self.editor.obstacles[idx]))
        elif pyglet.window.key.N == key:
            if len(self.obstacle.vertices) < 3 or not self.obstacle.check_vertex_valid():
                self.editor.set_statusline("Incomplete obstacle not saved. New obstacle created.", temp=True)
            elif self.obstacle not in self.editor.obstacles:
                self.editor.obstacles.append(self.obstacle)
                self.editor.set_statusline("Saved obstacle. New obstacle created.", temp=True)
            self.editor.pop_state()
            self.editor.push_state(ObstacleEditState(self.editor))

#------------------------------------------------------------------------------

class SplineEditState(EditorState):

    SPLINEGRABDIST = 10.0

    statusinfo = "Editing a spline."

    def __init__(self, editor, spline=None):
        self.editor = editor
        self.spline = spline
        self.camride = False
        self.camtime = 0
        self.camlast = None
        self.campoint = None
    def enter(self):
        if self.spline:
            self.lookat(self.spline.get_point(0))
        else:
            self.spline = lib.spline.Spline(self.editor)
        self.guide = None
        self.editor.set_statusline("Entered spline-mode. New spline created.", temp=True)
    def exit(self):
        pass
    def update(self, dt):
        if self.camride:
            for bullet in self.editor.bullets:
                bullet.update(dt)
            self.camtime += dt
            self.camlast = self.campoint
            self.campoint = self.spline.get_point(self.camtime)
            if not self.campoint:
                self.camtime = 0
            else:
                self.lookat(self.campoint)
                if self.camlast:
                    l = self.camlast
                    p = self.campoint
                    self.editor.bg_texture.anchor_x += -self.editor.DRAGSPEEDBGMOD * (l.x - p.x)
                    self.editor.bg_texture.anchor_y += -self.editor.DRAGSPEEDBGMOD * (l.y - p.y)
                
    def draw(self):
        self.spline.draw()
        if self.camride and self.campoint:
            pyglet.gl.glPointSize(12)
            pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                                 ('v2f', (self.campoint.x, self.campoint.y)),
                                 ('c3f', (.6, .48, .36)))
    def mouse_press(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if not self.guide:
                closest = self._get_closest(x,y)
                if closest:
                    self.guide = closest
                else:
                    self.spline.add_guide(x, y)
                    self.guide = self.spline.guides[-1]
        elif pyglet.window.mouse.RIGHT == button:
            closest = self._get_closest(x,y)
            if closest:
                self.spline.remove_guide(closest)
    def _get_closest(self, x, y):
        closest = None
        dist = self.SPLINEGRABDIST
        d = dist + 1
        for guide in self.spline.guides:
            try:
                d = Vec3(x, y).get_distance(Vec3(guide.x, guide.y))
            except ValueError, e:
                if __debug__: print e.message
                if __debug__: print x, y, guide.x, guide.y
                continue
            if d < dist:
                dist = d
                closest = guide
        if __debug__: print "Closest was", d
        return closest
    
    def mouse_release(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.guide:
                self.spline.move_guide(self.guide, x, y)
                self.guide = None
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.guide:
                self.spline.move_guide(self.guide, x, y)
    def key_press(self, key, modifiers):
        if pyglet.window.key.ENTER == key:
            if self.spline not in self.editor.splines:
                self.editor.splines.append(self.spline)
            self.editor.set_statusline("Saved spline. Left spline-mode.", temp=True)
            self.editor.pop_state()
        elif pyglet.window.key.TAB == key:
            if self.spline not in self.editor.splines:
                self.editor.splines.append(self.spline)
                idx = 0
            else:
                idx = self.editor.splines.index(self.spline) - 1
            self.editor.pop_state()
            self.editor.set_statusline("Viewing spline #%d" % idx, temp=True)
            self.editor.push_state(SplineEditState(self.editor, spline=self.editor.splines[idx]))
        elif pyglet.window.key.N == key:
            if self.spline not in self.editor.splines:
                self.editor.splines.append(self.spline)
            self.editor.pop_state()
            self.editor.push_state(SplineEditState(self.editor))
            self.editor.set_statusline("Saved previous spline. New spline created.", temp=True)
        elif pyglet.window.key.T == key:
            self.spline.kind += 1
            if self.spline.kind > 2:
                self.spline.kind = 0
            if self.spline.kind == 0:
                self.editor.set_statusline("Current spline set to WHITE.", temp=True)
            elif self.spline.kind == 1:
                self.editor.set_statusline("Current spline set to BLACK.", temp=True)
            elif self.spline.kind == 2:
                for spline in self.editor.splines:
                    if spline.kind == 2:
                        spline.kind = 0
                self.spline.kind = 2
                self.editor.set_statusline("Current spline set to CAMERA.", temp=True)
            self.spline.update_points()
        elif pyglet.window.key.C == key:
            if self.spline.kind == 2:
                self.camride = not self.camride
                for enemy in self.editor.enemies:
                    if self.camride:
                        enemy.fire_later()
                    else:
                        enemy.hold()
        elif pyglet.window.key.SPACE == key:
            if self.camride:
                self.camtime = 0
            
            
    
    def key_release(self, key, modifiers):
        pass

#------------------------------------------------------------------------------
class TriggerEditState(EditorState):

    SPLINEGRABDIST = 10.0

    statusinfo = "Editing a Trigger."

    def __init__(self, editor, trigger=None):
        self.editor = editor
        self.trigger = trigger

    def enter(self):
        if self.trigger:
            self.lookat(self.trigger.position)
        else:
            self.trigger = lib.obstacle.Trigger(self.editor.campos + Vec3(400,300), 100)
        self.guide = None
        self.editor.set_statusline("Entered triger-edit-mode. New trigger created.", temp=True)
    def exit(self):
        pass
    def update(self, dt):
        pass
                
    def draw(self):
        self.trigger.draw()
    def mouse_press(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.trigger:
                self.trigger.position.x = x
                self.trigger.position.y = y
                self.trigger.update_points()
        elif pyglet.window.mouse.RIGHT == button:
            if self.trigger:
                self.trigger.bounding_radius = (self.trigger.position - Vec3(x,y)).length
                self.trigger.update_points()
    def mouse_release(self, x, y, button, modifiers):
        pass
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            if self.trigger:
                self.trigger.position.x = x
                self.trigger.position.y = y
                self.trigger.update_points()
        elif pyglet.window.mouse.RIGHT == button:
            if self.trigger:
                self.trigger.bounding_radius = (self.trigger.position - Vec3(x,y)).length
                self.trigger.update_points()
    def key_press(self, key, modifiers):
        if pyglet.window.key.ENTER == key:
            if self.trigger not in self.editor.triggers:
                self.editor.triggers.append(self.trigger)
            self.editor.set_statusline("Saved trigger. Left trigger-mode.", temp=True)
            self.editor.pop_state()
        elif pyglet.window.key.S == key:
            if self.trigger:
                self.editor.set_statusline("Select a Spline!")
                self.editor.push_state(TriggerConnectionEditState(self.editor, self.trigger))
            else:
                self.editor.set_statusline("No Trigger to connect to!")

            
        elif pyglet.window.key.N == key:
            if self.trigger not in self.editor.triggers:
                self.editor.triggers.append(self.trigger)
            self.editor.pop_state()
            self.editor.push_state(TriggerEditState(self.editor))
            self.editor.set_statusline("Saved previous trigger. New Trigger created.", temp=True)
#        elif pyglet.window.key.C == key:
#            if self.spline.kind == 2:
#                self.camride = not self.camride
        elif pyglet.window.key.SPACE == key:
            if self.camride:
                self.camtime = 0
        elif pyglet.window.key.TAB == key:
            if self.trigger not in self.editor.triggers:
                self.editor.triggers.append(self.trigger)
                idx = 0
            else:
                idx = self.editor.triggers.index(self.trigger) - 1
            self.editor.pop_state()
            self.editor.set_statusline("Viewing trigger #%d" % idx, temp=True)
            self.editor.push_state(TriggerEditState(self.editor, trigger=self.editor.triggers[idx]))
    
    def key_release(self, key, modifiers):
        pass

#------------------------------------------------------------------------------
class TriggerConnectionEditState(EditorState):

    SPLINEGRABDIST = 10.0

    statusinfo = "Editing a Trigger."

    def __init__(self, editor, trigger):
        self.editor = editor
        self.trigger = trigger
        self.point2 = None

    def enter(self):
        self.editor.set_statusline("Select a Spline!", temp=False)
    def exit(self):
        pass
    def update(self, dt):
        pass
                
    def draw(self):
        if self.point2:
            pyglet.graphics.draw(2, pyglet.gl.GL_LINE_STRIP,
                     ('v2f', (self.trigger.position.x, self.trigger.position.y, self.point2.x, self.point2.y)),
                     ('c3f', (.6, .48, .36)*2))
        
    def mouse_press(self, x, y, button, modifiers):
        if pyglet.window.mouse.LEFT == button:
            self.point2 = Vec3(x,y)
            
            
    def mouse_release(self, x, y, button, modifiers):
        closest = self._get_closest(x,y)
        if closest:
            self.trigger += closest.on_trigger
            closest.trigger_uuids.append(self.trigger.uuid)
            self.editor.set_statusline("Connected!", temp=True)
        else:
            self.editor.set_statusline("missed!", temp=True)
        
    def _get_closest(self, x, y):
        closest = None
        dist = 100
        d = dist + 1
        for spline in self.editor.splines:
            for guide in spline.guides:
                try:
                    d = Vec3(x, y).get_distance(Vec3(guide.x, guide.y))
                except ValueError, e:
                    if __debug__: print e.message
                    if __debug__: print x, y, guide.x, guide.y
                    continue
                if d < dist:
                    dist = d
                    closest = spline
        if __debug__: print "Closest was", d
        return closest
        
    def mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.point2.x = x
        self.point2.y = y
    def key_press(self, key, modifiers):
        if pyglet.window.key.ENTER == key:
            self.editor.pop_state()
            self.editor.set_statusline("Leaving Connections.", temp=True)
    
    def key_release(self, key, modifiers):
        pass

#------------------------------------------------------------------------------

from lib.util import GameLevel
        
class EditorScene(lib.scenes.Scene):
    
    DRAGSPEEDMOD = 2.0
    DRAGSPEEDBGMOD = 0.1
    
    def __init__(self, app, level_number=0):
        super(EditorScene, self).__init__(app)
        self.states = []
        
        self.splines = []
        self.flocks = []
        self.obstacles = []
        self.enemies = []
        self.triggers = []
        self.bullets = []
        
        self.statusline = None
        self.status_changer = None
        self.set_statusline("Now editing level %d." % level_number)
        
        # Camera's in-world cordinate
        self.campos = Vec3(0.0, 0.0)
        
        self.bg_image = pyglet.image.load("data/textures/background.png")
        self.bg_texture = pyglet.image.TileableTexture.create_for_image(self.bg_image)
        self.level_number = level_number
        
        
        self.textures = []
        for root, dirs, files in os.walk('data/textures/level'):
           for name in files:       
               filename = os.path.join(root, name)
               if filename.lower().endswith('.png'):
                self.textures.append((filename, pyglet.image.load(filename).texture))
        self.current_texture = self.textures[0]
        self.texture_batch = pyglet.graphics.Batch()
        
        self.load_level()
        
        
    def get_next_texture(self):
        idx = 0
        for i, texture in enumerate(self.textures):
            if texture[0] == self.current_texture:
                idx = i
                break;
        self.current_texture = [idx-1][0]
        return self.textures[idx-1]
         
    def get_current_texture(self):
        return self.get_texture(self.current_texture)
        
    def get_texture(self, name):
        for text in self.textures:
            if text[0] == name:
                return text
        
    def lookat(self, pos):
        self.campos = pos - CAMOFF   
        
    def save_level(self):
        level = GameLevel()
        level.splines = [s.get_serialized() for s in self.splines]
        level.triggers = [t.get_serialized() for t in self.triggers]
        level.obstacles = [o.get_serialized() for o in self.obstacles]
        level.enemies = [e.get_serialized() for e in self.enemies]
        cerealizer.dump(level, open("data/%d_level.lvl" % self.level_number, "wb"))
        
    def load_level(self):
        self.level_file = "data/%d_level.lvl" % self.level_number
        level = None
        try:
            fobj = open(self.level_file, "rb")
            level = cerealizer.load(fobj)
        except:
            return
        if level:
            self.splines = [spline.Spline(self, serial=s) for s in level.splines]
            self.triggers = [obstacle.Trigger(0, 0, serial=t) for t in level.triggers]
            self.obstacles = [obstacle.Polygon(self, self.texture_batch, serial=o) for o in level.obstacles]
            self.enemies = [enemies.Enemy(self, s.fire_rate, s.position, s.orientation) for s in level.enemies]
            # connect triggers
            for spl in self.splines:
                for trigger_uuid in spl.trigger_uuids:
                    for trigger in self.triggers:
                        if trigger.uuid == trigger_uuid:
                            trigger += spl.on_trigger

    def add_dynamic(self, entity):
        if isinstance(entity, enemies.Bullet):
            self.bullets.append(entity)
        elif isinstance(entity, flock.Flock):
            self.flocks.append(entity)
        else:
            if __debug__: print 'UNKNOWN  entity type to add', entity.__class__.__name__

    def remove_dynamic(self, entity):
        try:
            if isinstance(entity, enemies.Bullet):
                self.bullets.remove(entity)
            elif isinstance(entity, flock.Flock):
                self.flocks.remove(entity)
            else:
                if __debug__: print 'UNKNOWN entity type to remove', entity.__class__.__name__
        except:
            pass

    def push_state(self, state):
        self.states.append(state)
        state.enter()
        
    def pop_state(self):
        if self.states:
            old = self.states.pop()
            old.exit()
            
    def set_statusline(self, message, temp=False):
        self.statusline = pyglet.text.Label(": " + str(message),
                            font_name='System',
                            font_size=12,
                            x=0, y=3,
                            color=(86,86,86, 255))
        if temp:
            pyglet.clock.unschedule(self.status_update)
            pyglet.clock.schedule_once(self.status_update, 3)
            
    def status_update(self, dt):
        if not self.states:
            self.set_statusline("Idle.")
        else:
            if hasattr(self.states[-1], "statusinfo"):
                self.set_statusline(self.states[-1].statusinfo)
                
    def on_scene_enter(self):
        glClearColor(.2, .2, .2, 1.0)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_TEXTURE_2D)
        pyglet.clock.schedule(self.update)
        
    def on_scene_leave(self):
        #glDisable(GL_POINT_SMOOTH)
        #glDisable(GL_TEXTURE_2D)
        pyglet.clock.unschedule(self.update)
        
    def update(self, dt):
        if self.states:
            self.states[-1].update(dt)
            
    def draw_status(self):
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self.app.width, 0, self.app.height, -1, 1)
        
        self.statusline.draw()
        gl.glPopMatrix()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        
    def on_draw(self):
        self.app.clear()
        glLoadIdentity()
        # Background
        self.bg_texture.blit_tiled(0, 0, 0, 800, 600)
        self.draw_status()
        # Camera translation
        glTranslatef(-self.campos.x, -self.campos.y, 0.0)
        # Draw objects
        for spline in self.splines:
            spline.draw()
        for flock in self.flocks:
            flock.draw()
        #for obstacle in self.obstacles:
        #    obstacle.update_colors()
        #    obstacle.draw()
        self.texture_batch.draw()
        for trigger in self.triggers:
            trigger.draw()
        for enemy in self.enemies:
            enemy.draw()
        for bullet in self.bullets:
            bullet.draw()
        if self.states:
            self.states[-1].draw()

            
    def pan_camera(self, dx, dy, rate=1.0):
        self.campos += rate * (Vec3(dx, dy))
        self.bg_texture.anchor_x += self.DRAGSPEEDBGMOD * rate * dx
        self.bg_texture.anchor_y += self.DRAGSPEEDBGMOD * rate * dy
            
    def on_mouse_press(self, x, y, button, modifiers):
        if __debug__: print "Campos:", self.campos
        if __debug__: print "Raw X,Y:", x, y
        x += self.campos.x
        y += self.campos.y
        if __debug__: print "Adjusted X,Y:", x, y
        self.lastmousepos = Vec3(x, y)
        if self.states:
            self.states[-1].mouse_press(x, y, button, modifiers)
            
    def on_mouse_release(self, x, y, button, modifiers):
        x += self.campos.x
        y += self.campos.y
        self.lastmousepos = Vec3(x, y)
        if self.states:
            self.states[-1].mouse_release(x, y, button, modifiers)
            
    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        x += self.campos.x
        y += self.campos.y
        self.lastmousepos = Vec3(x, y)
        # Builtin
        if pyglet.window.mouse.MIDDLE == button:
            rate = 1.0
            if modifiers & pyglet.window.key.MOD_SHIFT:
                rate = self.DRAGSPEEDMOD
            self.pan_camera(-dx, -dy, rate=rate)
        elif self.states:
            self.states[-1].mouse_drag(x, y, dx, dy, button, modifiers)
            
    def on_mouse_motion(self, x, y, dx, dy):
        x += self.campos.x
        y += self.campos.y
        self.lastmousepos = Vec3(x, y)
                
    def on_key_press(self, key, modifiers):
        if self.states:
            self.states[-1].key_press(key, modifiers)
        else:
            if key == pyglet.window.key.S and modifiers & pyglet.window.key.MOD_CTRL:
                spline = None
                if self.splines:
                    spline = self.splines[-1]
                self.push_state(SplineEditState(self, spline))
            elif key == pyglet.window.key.X and modifiers & pyglet.window.key.MOD_CTRL:
                obstacle = None
                if self.obstacles:
                    obstacle = self.obstacles[-1]
                self.set_statusline("Entered obstacle-mode." )
                self.push_state(ObstacleEditState(self, obstacle))
            elif key == pyglet.window.key.T and modifiers & pyglet.window.key.MOD_CTRL:
                trigger = None
                if self.triggers:
                    trigger = self.triggers[-1]
                self.push_state(TriggerEditState(self, trigger))
            elif key == pyglet.window.key.E and modifiers & pyglet.window.key.MOD_CTRL:
                enemy = None
                if self.enemies:
                    enemy = self.enemies[-1]
                self.set_statusline("Entered enemy-mode.")
                self.push_state(EnemyEditState(self, enemy))
            elif key == pyglet.window.key.C:
                for spline in self.splines:
                    if spline.kind == 2:
                        self.push_state(SplineEditState(self, spline))
            elif key == pyglet.window.key.PAGEDOWN:
                self.save_level()
                self.app.pop_scene()
                self.app.push_scene(self.__class__, self.level_number + 1)
            elif key == pyglet.window.key.PAGEUP:
                self.save_level()
                if self.level_number > 0:
                    self.app.pop_scene()
                    self.app.push_scene(self.__class__, self.level_number - 1)
            elif key == pyglet.window.key.P:
                self.save_level()
                self.set_statusline("Level saved.")
                
            
            
    def on_key_release(self, key, modifiers):
        if self.states:
            self.states[-1].key_release(key, modifiers)
            
scene_class = EditorScene

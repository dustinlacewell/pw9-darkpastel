import pyglet
from pyglet.gl import *
from pyglet.window.key import *

from lib import scenes
from lib.spline import *

class SplineTestScene(scenes.Scene):

    def on_scene_enter(self):
       self.points = []
       pyglet.clock.schedule(self.update)
       
    def update(self, dt): pass
         
    def on_draw(self):
        self.app.clear()

        P = self.points
        l = len(P)

        pyglet.gl.glPointSize(5)
        for i in range(l):
            p = P[i]
            if i == 0:
                color = (0.0, 0.0, 1.0, 1.0)
            elif i == l - 1:
                color = (0.0, 1.0, 0.0, 1.0)
            else:
                color = (1.0, 0.0, 0.0, 1.0)
            pyglet.graphics.draw(1, pyglet.gl.GL_POINTS, ('v2f', (p.x, p.y)), ('c4f', color))
        pyglet.gl.glPointSize(1)

        verts = []
        if l < 4:
            return
        for j in range( 1, l - 2 ):
            for t in range( 20 ):
                p = spline_4p( t / 20.0, P[j - 1], P[j], P[j + 1], P[j + 2] )
                verts.extend([p.x, p.y])
                
        pyglet.graphics.draw(len(verts) / 2, pyglet.gl.GL_POINTS, ('v2f', verts))
        self.app.draw_fps()
        
    def on_mouse_press(self, x, y, button, modifiers):
        self.points.append(Point(x, y))
        
scene_class = SplineTestScene

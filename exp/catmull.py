'''
Ideas:
    The starting and ending guides of a spline should indicate its action.
    Icon, color, overlayed symbol/numbers.
    Actions:
        create flock (with r birds going s speed) (repeat x times every y seconds)
        detroy flock on touch
        bounce flocks back the other way
        stop flocksy
        etc.

    The line color should indicate the type of bird being created.
'''

import pyglet

from mathew import Vector2d

class Spline:
    # Would like to get rid of the Vector2d dependency.
    # Need to clean up the code and generalize colors.
    # Possilby make guides a class.
    def __init__(self, batch=None):
        self.guides = []
        self.batch = batch or pyglet.graphics.Batch()
        self.pvl = self.batch.add(1, pyglet.gl.GL_LINE_STRIP, None,
                                 ('v2f', (0, 0)),
                                 ('c3f', (0, 0, 0)))
        self.gvl = self.batch.add(1, pyglet.gl.GL_POINTS, None,
                                  ('v2f', (-100, -100)),
                                  ('c3f', (0, 0, 0)))

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
            points.extend([gpoints[-2], gpoints[-1]])
            self.pvl.resize(len(points) / 2)
            self.pvl.vertices = points
            self.pvl.colors = (.6, .6, .6) * (len(points) / 2)

    def add_guide(self, x, y):
        self.guides.append(Vector2d(x, y))
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

    def get_point(self, distance):
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
        pyglet.gl.glPointSize(5)
        self.batch.draw()

class Window(pyglet.window.Window):
    def __init__(self):
        super(Window, self).__init__(1000, 600, vsync=False)
        pyglet.gl.glClearColor(.2, .2, .2, 1.0)
        pyglet.gl.glEnable(pyglet.gl.GL_POINT_SMOOTH)

        pyglet.clock.schedule(self.update)
        self.fps = pyglet.clock.ClockDisplay()

        self.spline = Spline()
        self.p = None
        self.t = 0
        self.moving = False

    def update(self, dt):
        if self.moving == True:
            self.t += dt
            self.p = self.spline.get_point(self.t)
        if not self.p:
            self.t = 0

    def on_mouse_press(self, x, y, button, modifiers):
        self.spline.add_guide(x, y)

    def on_key_press(self, symbol, modifier):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        elif symbol == pyglet.window.key.SPACE:
            self.moving = not self.moving

    def on_draw(self):
        self.clear()
        self.fps.draw()
        self.spline.draw()
        if not self.p:
            return
        pyglet.gl.glPointSize(12)
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                             ('v2f', (self.p.x, self.p.y)),
                             ('c3f', (.6, .48, .36)))

if __name__ == '__main__':
    window = Window()
    pyglet.app.run()

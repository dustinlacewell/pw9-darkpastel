import pyglet
from pyglet.gl import *
from pyglet.window.key import *

from lib import scenes
from lib.spline import *
import lib.util
from lib.util import Rect

class SplineTestScene(scenes.Scene):

    def on_scene_enter(self):
        self.points = []
        pyglet.clock.schedule(self.update)
        self.buttons = []
        self.hover_idx = 0
        # create buttons
        self.buttons.append(self.create_button('new', 400, 70*4, self.on_btn_new))
        if self.app.read_progress(): self.buttons.append(self.create_button('continue', 400, 70 *3, self.on_btn_continue))
        self.buttons.append(self.create_button('exit', 400, 70*2, self.on_btn_exit))
        if __debug__: self.buttons.append(self.create_button('edit', 400, 70, self.on_btn_editor))
        self._btn = None
        # at the end
        self.buttons[self.hover_idx].state = 1
        self.bg_image = pyglet.image.load("data/textures/background.png")
        self.bg_texture = pyglet.image.TileableTexture.create_for_image(self.bg_image)
        self.logo = pyglet.sprite.Sprite(pyglet.image.load("data/img/logo.png"))
        self.logo.x = 0
        self.logo.y = 300
        self.pan_speed = 10
        
        #glEnable(GL_TEXTURE_2D)
        #glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
    def create_buttons(self):
        self.buttons = []
        self.buttons.append(self.create_button('new', 400, 70*4, self.on_btn_new))
        if self.app.read_progress(): self.buttons.append(self.create_button('continue', 400, 70 *3, self.on_btn_continue))
        self.buttons.append(self.create_button('exit', 400, 70*2, self.on_btn_exit))
        if __debug__: self.buttons.append(self.create_button('edit', 400, 70, self.on_btn_editor))
        self.buttons[self.hover_idx].state = 1
    def pan_camera(self, dx, dy, rate=1.0):
        self.bg_texture.anchor_x +=  rate * dx
        self.bg_texture.anchor_y += rate * dy
        
    def on_scene_leave(self):
        #glDisable(GL_TEXTURE_2D)
        #glDisable(GL_BLEND)
        pyglet.clock.unschedule(self.update)

    def on_scene_pause(self):
        pyglet.clock.unschedule(self.update)

    def on_scene_resume(self):
        print "I!!#RE!#RJO!#J"
        self.pan_speed = 10
        pyglet.clock.schedule(self.update)
    

    def create_button(self, text, x, y, callback):
        class B(object): pass
        btn = B()
        font_name = 'Times New Roman'
        font_size=36
        label = pyglet.text.Label(text, font_name=font_name, font_size=font_size, \
                                        x=x, y=y, width=300, height=50, anchor_x="center")
        btn.normal = label
        label = pyglet.text.Label(text, font_name=font_name, font_size=font_size, \
                                        x=x, y=y, width=300, height=50, anchor_x="center", color=(255,255,0,255))
        btn.hover = label
        label = pyglet.text.Label(text, font_name=font_name, font_size=font_size, \
                                        x=x, y=y, width=300, height=50, anchor_x="center", color=(255,0,0,255))
        btn.pressed = label
        btn.rect = Rect(label.x - label.width // 2, label.y, label.width, label.height)
        btn.callback = callback
        btn.state = 0
        return btn

    def draw_btn(self, btn):
        if btn.state == 0: # normal
            btn.normal.draw()
        elif btn.state == 1: # hover
            btn.hover.draw()
        else:
            btn.pressed.draw()

    #-- button callbacks --#
    def on_btn_new(self):
        self.app.push_scene(scenes.get('playlevelscene'), 0)
        
    def on_btn_continue(self):
        level = self.app.read_progress()
        self.app.push_scene(scenes.get('playlevelscene'), level)

    def on_btn_exit(self):
        exit()
        
    def on_btn_editor(self):
        self.app.push_scene(scenes.get('editorscene'))
        
    #-- update and draw --#
    def update(self, dt):
        self.pan_camera(self.pan_speed*dt, 0.0*dt)
         
    def on_draw(self):
        glLoadIdentity()
        self.app.clear()
        # Background
        self.bg_texture.blit_tiled(0, 0, 0, 800, 600)
        self.logo.draw()
        for btn in self.buttons:
            self.draw_btn(btn)

        self.app.draw_fps()

    #-- event handling --#
    def on_scene_resume(self):
        self.create_buttons()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._btn:
            if self._btn.rect.collidepoint((x,y)):
                self._btn.state = 2
            else:
                self._btn.state = 0

    def on_mouse_motion(self, x, y, dx, dy):
        hit = False
        for btn in self.buttons:
            btn.state = 0
            if btn.rect.collidepoint((x,y)):
                hit = True
                self.pan_speed += 10
                self.pan_speed = min(1000000, self.pan_speed)
                btn.state = 1
                self.hover_idx = self.buttons.index(btn)
        if not hit:
            self.pan_speed = 10
    def on_mouse_press(self, x, y, button, modifiers):
        for btn in self.buttons:
            if btn.rect.collidepoint((x,y)):
                btn.state = 2
                self._btn = btn

    def on_mouse_release(self, x, y, button, modifiers):
        if self._btn and self._btn.rect.collidepoint((x,y)):
            self._btn.callback()
            self._btn.state = 1
            self.hover_idx = self.buttons.index(self._btn)
        self._btn = None
        
    def on_key_press(self, symbol, modifiers):
        self.buttons[self.hover_idx].state = 0
        if symbol == ENTER:
            self.buttons[self.hover_idx].state = 2
        elif symbol == UP:
            self.hover_idx -= 1
            if self.hover_idx < 0:
                self.hover_idx = len(self.buttons)-1
        elif symbol == DOWN:
            self.hover_idx += 1
            if self.hover_idx >= len(self.buttons):
                self.hover_idx = 0
        elif symbol == F5:
            # secret test playground
            self.app.push_scene(scenes.get('playgroundscene'))
        if self.buttons[self.hover_idx].state < 2:
            self.buttons[self.hover_idx].state = 1

    def on_key_release(self, symbol, modifiers):
        if symbol == ENTER:
            self.buttons[self.hover_idx].callback()
        self.buttons[self.hover_idx].state = 1
            
scene_class = SplineTestScene

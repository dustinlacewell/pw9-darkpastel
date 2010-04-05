import pyglet
import pyglet.window
import pyglet.clock
import pyglet.app
from pyglet.gl import *

class ApplicationClass(pyglet.window.Window):

    def __init__(self, *args, **named):
        super(ApplicationClass, self).__init__(**named)
        # Event handlers
        self.register_event_type('on_scene_pause')
        self.register_event_type('on_scene_resume')
        self.register_event_type('on_scene_enter')
        self.register_event_type('on_scene_leave')
        self.event_loop = pyglet.app.EventLoop()
        self.event_loop.push_handlers(self)
        # Scene attributes
        self.scenes = []
        self.current_scene = None
        self.first_scene = None
        # Clock attributes
        self.fps_display = pyglet.clock.ClockDisplay()
        
    def write_progress(self, level = 0):
        f = open('data/progress', 'w')
        f.write(str(level))
        
    def read_progress(self):
        try:
            f = open('data/progress', 'r')
            return int(f.read())
        except Exception, e:
            return 0
    def draw_fps(self):
        self.fps_display.draw()
        
    def push_scene(self, scene, *args, **named):
        if self.current_scene:
            self.scenes.append(self.current_scene)
            self.dispatch_event('on_scene_pause')
            try: self.pop_handlers()
            except: pass
        self.current_scene = scene(self, *args, **named)
        self.push_handlers(self.current_scene)
        self.dispatch_event('on_scene_enter')

    def swap_scene(self, scene):
        if self.current_scene:
            self.dispatch_event('on_scene_leave')
            try: self.pop_handlers()
            except: pass
        self.current_scene = scene
        self.push_handlers(self.current_scene)
        self.dispatch_event('on_scene_enter')
        
    def pop_scene(self):
        if self.current_scene:
            self.dispatch_event('on_scene_leave')
            try: self.pop_handlers()
            except:
                pass
            try:
                self.current_scene = self.scenes.pop()
                self.push_handlers( self.current_scene )
                self.dispatch_event('on_scene_resume')
            except Exception, e:
                self.event_loop.exit()
                #self.on_close()
        
    def run(self, scene):
        self.first_scene = scene
        self.event_loop.run()
    
    def on_enter(self):
        self.push_scene( self.first_scene )
        self.set_visible()
        self.first_scene = None
    
    def on_close(self):
        self.pop_scene()
        #self.event_loop.exit()

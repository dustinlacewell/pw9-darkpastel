import lib.util

loaded_scene_classes = {}

class Scene(object):    def __init__(self, app):
        self.app = app
    def on_scene_enter(self): pass
    def on_scene_pause(self): pass    
    def on_scene_resume(self): pass
    def on_scene_leave(self): pass     
    def on_draw(self):
        self.app.clear()
        self.app.draw_fps()

def get( scene_name ):
    if scene_name in loaded_scene_classes:
        return loaded_scene_classes[ scene_name ]
    fullpath = '.'.join( [__name__, scene_name, 'scene_class'] )
    cls = lib.util.get_class(fullpath, parentClass = Scene)
    if cls:
        loaded_scene_classes[ scene_name ] = cls
        return cls
    else:
        return None

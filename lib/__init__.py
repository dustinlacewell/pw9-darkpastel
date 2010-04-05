#---- requirements ----#
def _requires_pyglet_version(version):
    try:
        import pyglet
        req = [int(i) for i in version if i in '1234567890']
        have = [int(i) for i in pyglet.version if i in '1234567890']
        if tuple(req) > tuple(have):
            raise ImportError('This game requires Pyglet %s or later' % version)
    except ImportError:
        raise ImportError('This requires Pyglet %s or later' % version)
        
_requires_pyglet_version('1.1')


import lib.app, lib.scenes

def main():

    application = lib.app.ApplicationClass(width=800, height=600, vsync=False)
    first_scene = lib.scenes.get('menuscene')
    application.run( first_scene )


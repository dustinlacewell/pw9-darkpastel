import time, random, md5
import cerealizer, pyglet
from pyglet.gl import *


def _gen():
    num = 0
    while True:
        num += 1
        yield num
_g = _gen()

class TextureEnableGroup(pyglet.graphics.Group):
    def set_state(self):
        glEnable(GL_TEXTURE_2D)

    def unset_state(self):
        glDisable(GL_TEXTURE_2D)

texture_enable_group = TextureEnableGroup()

class TextureBindGroup(pyglet.graphics.Group):
    def __init__(self, texture):
        super(TextureBindGroup, self).__init__(parent=texture_enable_group)
        assert texture.target == GL_TEXTURE_2D
        self.texture = texture

    def set_state(self):
        glBindTexture(GL_TEXTURE_2D, self.texture.id)

    # No unset_state method required.

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.texture == other.__class__)

    
def uuid( *args ):
  """
    Generates a universally unique ID.
    Any arguments only create more randomness.
  """
  return _g.next()
    
#  t = long( time.time() * 1000 )
#  r = long( random.random()*100000000000000000L )
#  try:
#    a = socket.gethostbyname( socket.gethostname() )
#  except:
#    # if we can't get a network address, just imagine one
#    a = random.random()*100000000000000000L
#  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
#  data = md5.md5(data).hexdigest()
#  return data

class GameLevel(object):
    def __init__(self):
        self.splines = []
        self.triggers = []
        self.obstacles = []
        self.enemies = []
        self.triggers = []
        
cerealizer.register_class(GameLevel)

def get_mod(modulePath):
    return __import__(modulePath, globals(), locals(), ['*'])

def get_attr(fullAttrName):
    """Retrieve a module attribute from a full dotted-package name."""
    # Parse out the path, module, and function
    lastDot = fullAttrName.rfind(u".")
    attrName = fullAttrName[lastDot + 1:]
    modPath = fullAttrName[:lastDot]
    aMod = get_mod(modPath)
    aAttr = getattr(aMod, attrName)
    # Return a reference to the function itself,
    # not the results of the function.
    return aAttr
    
def get_func(fullFuncName):
    aFunc = get_attr(fullFuncName)
    assert callable(aFunc), "%s is not callable." % fullFuncName
    return aFunc

def get_class(fullClassName, parentClass=None):
    """Load a module and retrieve a class (NOT an instance).
    
    If the parentClass is supplied, className must be of parentClass
    or a subclass of parentClass (or None is returned).
    """
    aClass = get_func(fullClassName)
    
    # Assert that the class is a subclass of parentClass.
    if parentClass is not None:
        if not issubclass(aClass, parentClass):
            raise TypeError(u"%s is not a subclass of %s" %
                            (fullClassName, parentClass))
    
    # Return a reference to the class itself, not an instantiated object.
    return aClass

class Rect(object):

    def __init__(self, x, y, w, h):
        assert x+w > x
        assert y+h > y
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    def _set_right(self, r):
        assert r > self.x
        self.w = r - self.x
    right = property(lambda self: self.x + self.w, _set_right)
    
    def _set_top(self, t):
        assert t > self.y
        self.h = t - self.y
    top = property(lambda self: self.y + self.h, _set_top)
    
    def _set_centerx(self, x):
        w = self.w // 2
        self.x = x - w
    centerx = property(lambda self: self.x + self.w // 2, _set_centerx)

    def _set_centery(self, y):
        h = self.h // 2
        self.y = y - h
    centerx = property(lambda self: self.y + self.h // 2, _set_centery)

    def _set_center(self, c):
        x, y = c
        self.x = x - self.w // 2
        self.y = y - self.h // 2
    center = property(lambda self: (self.centerx, self.centery), _set_center)
    
    def collidepoint(self, (x,y)):
        if x < self.x: return False
        if x > self.right: return False
        if y < self.y: return False
        if y > self.top: return False
        return True
    
    def colliderect(self, other):
        #if other.x > self.right or other.right < self.x or other.y > self.top or other.top < self.y: return False
        #return True
        if not (other.x > self.right or other.right < self.x or other.y > self.top or other.top < self.y): return True
        return False

    def collidelist(self, others):
        for idx, other in enumerate(others):
            if not (other.x > self.right or other.right < self.x or other.y > self.top or other.top < self.y):
                return idx

    def collidelistall(self, others):
        return [idx for idx, other in enumerate(others) if not (other.x > self.right or other.right < self.x or other.y > self.top or other.top < self.y)]

    def move(self, dx, dy):
        return self.__class__(x, y, self.w, self.h)
        
    def move_ip(self, dx, dy):
        self.x += dx
        self.y += dy

    def __str__(self):
        return "<rect(%s, %s, %s, %s)>" % (str(self.x), str(self.y), str(self.w), str(self.h))

if __name__ == '__main__':
    
    r = Rect(10, 10, 10, 10)
    print True == r.collidepoint((11,11))
    print False == r.collidepoint((5,11))
    print False == r.collidepoint((25,11))
    print False == r.collidepoint((11,1))
    print False == r.collidepoint((11,30))
    print False == r.collidepoint((5,5))
    print False == r.collidepoint((35,35))
    print False == r.collidepoint((35,5))
    print False == r.collidepoint((5,35))
    
    print False == r.colliderect(Rect( 1, 1, 5, 5))
    print False == r.colliderect(Rect(11, 1, 5, 5))
    print False == r.colliderect(Rect(31, 1, 5, 5))
    print False == r.colliderect(Rect(1, 11, 5, 5))
    print False == r.colliderect(Rect(31, 11, 5, 5))
    print False == r.colliderect(Rect( 1, 31, 5, 5))
    print False == r.colliderect(Rect(11, 31, 5, 5))
    print False == r.colliderect(Rect(31, 31, 5, 5))

    print True == r.colliderect(Rect( 8, 8, 5, 5))
    print True == r.colliderect(Rect(11, 8, 5, 5))
    print True == r.colliderect(Rect(18, 8, 5, 5))
    print True == r.colliderect(Rect( 8, 11, 5, 5))
    print True == r.colliderect(Rect(11, 11, 5, 5))
    print True == r.colliderect(Rect(18, 11, 5, 5))
    print True == r.colliderect(Rect( 8, 18, 5, 5))
    print True == r.colliderect(Rect(11, 18, 5, 5))
    print True == r.colliderect(Rect(18, 18, 5, 5))
    
    rects = [Rect( 1,  1, 5, 5), Rect(11,  1, 5, 5), 
             Rect(31,  1, 5, 5), Rect( 1, 11, 5, 5), 
             Rect(31, 11, 5, 5), Rect( 1, 31, 5, 5), 
             Rect(11, 31, 5, 5), Rect(31, 31, 5, 5), 
             
             Rect( 8,  8, 5, 5), Rect(11,  8, 5, 5), 
             Rect(18,  8, 5, 5), Rect( 8, 11, 5, 5), 
             Rect(11, 11, 5, 5), Rect(18, 11, 5, 5), 
             Rect( 8, 18, 5, 5), Rect(11, 18, 5, 5), 
             Rect(18, 18, 5, 5)]
    
    print [8, 9, 10, 11, 12, 13, 14, 15, 16] == r.collidelistall(rects)
    print 8 == r.collidelist(rects)
    print r

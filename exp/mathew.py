import operator

class Vector2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return 'Vector2d(%s, %s)' % (self.x, self.y)

    def __add__(self, other):
        try:
            return Vector2d(self.x + other.x, self.y + other.y)
        except:
            return Vector2d(self.x + other, self.y + other)

    __radd__ = __add__

    def __mul__(self, other):
        try:
            return Vector2d(self.x * other.x, self.y * other.y)
        except:
            return Vector2d(self.x * other, self.y * other)
        
    __rmul__ = __mul__

    def __div__(self, other):
        try:
            return Vector2d(operator.div(self.x, other.x),
                            operator.div(self.y, other.y))
        except:
            return Vector2d(operator.div(self.x, other),
                            operator.div(self.y, other))

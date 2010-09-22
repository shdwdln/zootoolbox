'''
super simple vector class and vector functionality.  i wrote this simply because i couldn't find
anything that was easily accessible and quick to write.  this may just go away if something more
comprehensive/mature is found
'''

import re
import math
import random
from math import cos, sin, tan, acos, asin, atan2


sqrt = math.sqrt
zeroThreshold = 1e-8

class MatrixException(Exception):
	pass


class Angle(object):
	def __init__( self, angle, radian=False ):
		'''set the radian to true on init if the angle is in radians - otherwise degrees are assumed'''
		if radian:
			self.radians = angle
			self.degrees = math.degrees(angle)
		else:
			self.degrees = angle
			self.radians = math.radians(angle)


class Vector(list):
	'''
	provides a bunch of common vector functionality.  Vectors must be instantiated a list/tuple of values.
	If you need to instantiate with items, use the Vector.FromValues like so:
	Vector.FromValues(1,2,3)
	'''

	@classmethod
	def FromValues( cls, *a ):
		return cls( a )

	def __repr__( self ):
		return '<%s>' % ', '.join( '%0.3g' % v for v in self )
	__str__ = __repr__
	def setIndex( self, idx, value ):
		self[ idx ] = value
	def __nonzero__( self ):
		for item in self:
			if item:
				return True

		return False
	def __add__( self, other ):
		return self.__class__( [x+y for x, y in zip(self, other)] )
	__iadd__ = __add__
	def __radd__( self, other ):
		return self.__class__( [x+y for x, y in zip(other, self)] )
	def __sub__( self, other ):
		return self.__class__( [x-y for x,y in zip(self, other)] )
	def __mul__( self, factor ):
		'''
		supports either scalar multiplication, or vector multiplication (dot product).  for cross product
		use the .cross( other ) method which is bound to the rxor operator.  ie: a ^ b == a.cross( b )
		'''
		if isinstance( factor, (int, float) ):
			return self.__class__( [x * factor for x in self] )
		elif isinstance( factor, Matrix ):
			return multVectorMatrix( self, factor )

		#assume its another vector then
		value = self[0] * factor[0]
		for x, y in zip( self[1:], factor[1:] ):
			value += x*y

		return value
	def __div__( self, denominator ):
		return self.__class__( [x / denominator for x in self] )
	def __neg__( self ):
		return self.__class__( [-x for x in self] )
	__invert__ = __neg__
	def __eq__( self, other, tolerance=1e-5 ):
		'''
		overrides equality test - can specify a tolerance if called directly.
		NOTE: other can be any iterable
		'''
		for a, b in zip(self, other):
			if abs( a - b ) > tolerance:
				return False

		return True
	within = __eq__
	def __ne__( self, other, tolerance=1e-5 ):
		return not self.__eq__( other, tolerance )
	def __mod__( self, other ):
		return self.__class__( [x % other for x in self] )
	def __int__( self ):
		return int( self.get_magnitude() )
	def __hash__( self ):
		return hash( tuple( self ) )
	@classmethod
	def Zero( cls, size=3 ):
		return cls( ([0] * size) )
	@classmethod
	def Random( cls, size=3, valueRange=(0,1) ):
		return cls( [random.uniform( *valueRange ) for n in range( size )] )
	@classmethod
	def Axis( cls, axisName, size=3 ):
		'''
		returns a vector from an axis name - the axis name can be anything from the Vector.INDEX_NAMES
		list.  you can also use a - sign in front of the axis name
		'''
		axisName = axisName.lower()
		isNegative = axisName.startswith('-') or axisName.startswith('_')

		if isNegative:
			axisName = axisName[1:]

		new = cls.Zero( size )
		val = 1
		if isNegative:
			val = -1

		new.__setattr__( axisName, val )

		return new
	def dot( self, other, preNormalize=False ):
		a, b = self, other
		if preNormalize:
			a = self.normalize()
			b = other.normalize()

		dot = sum( [x*y for x,y in zip(a, b)] )

		return dot
	def __rxor__( self, other ):
		'''
		used for cross product - called using a**b
		NOTE: the cross product is only defined for a 3 vector
		'''
		x = self[1] * other[2] - self[2] * other[1]
		y = self[2] * other[0] - self[0] * other[2]
		z = self[0] * other[1] - self[1] * other[0]

		return self.__class__( [x, y, z] )
	cross = __rxor__
	def get_squared_magnitude( self ):
		'''
		returns the square of the magnitude - which is about 20% faster to calculate
		'''
		m = 0
		for val in self:
			m += val**2

		return m
	def get_magnitude( self ):

		#NOTE: this implementation is faster than sqrt( sum( [x**2 for x in self] ) ) by about 20%
		m = 0
		for val in self:
			m += val**2

		return sqrt( m )
	__float__ = get_magnitude
	__abs__ = get_magnitude
	length = magnitude = get_magnitude
	def set_magnitude( self, factor ):
		'''
		changes the magnitude of this instance
		'''
		factor /= self.get_magnitude()
		for n in range( len( self ) ):
			self[n] *= factor
	def normalize( self ):
		'''
		returns a normalized vector
		'''

		#inline the code for the SPEEDZ - its about 8% faster by inlining the code to calculate the magnitude
		mag = 0
		for v in self:
			mag += v**2

		mag = sqrt( mag )

		return self.__class__( [v / mag for v in self] )
	def change_space( self, basisX, basisY, basisZ=None ):
		'''
		will re-parameterize this vector to a different space
		NOTE: the basisZ is optional - if not given, then it will be computed from X and Y
		NOTE: changing space isn't supported for 4-vectors
		'''
		if basisZ is None:
			basisZ = basisX ^ basisY
			basisZ = basisZ.normalize()

		dot = self.dot
		new = dot( basisX ), dot( basisY ), dot( basisZ )

		return self.__class__( new )
	def rotate( self, quat ):
		'''
		Return the rotated vector v.

        The quaternion must be a unit quaternion.
        This operation is equivalent to turning v into a quat, computing
        self*v*self.conjugate() and turning the result back into a vec3.
        '''
		ww = quat.w * quat.w
		xx = quat.x * quat.x
		yy = quat.y * quat.y
		zz = quat.z * quat.z
		wx = quat.w * quat.x
		wy = quat.w * quat.y
		wz = quat.w * quat.z
		xy = quat.x * quat.y
		xz = quat.x * quat.z
		yz = quat.y * quat.z

		newX = ww * self.x + xx * self.x - yy * self.x - zz * self.x + 2*((xy-wz) * self.y + (xz+wy) * self.z)
		newY = ww * self.y - xx * self.y + yy * self.y - zz * self.y + 2*((xy+wz) * self.x + (yz-wx) * self.z)
		newZ = ww * self.z - xx * self.z - yy * self.z + zz * self.z + 2*((xz-wy) * self.x + (yz+wx) * self.y)

		return self.__class__( [newX, newY, newZ] )
	def complex( self ):
		return self.__class__( [ complex(v) for v in tuple(self) ] )
	def conjugate( self ):
		return self.__class__( [ v.conjugate() for v in tuple(self.complex()) ] )

	#this is kinda dumb - it'd be nice if this could be auto-derived from the value of INDEX_NAMES but I couldn't get it working so...  meh
	x = property( lambda self: self[ 0 ], lambda self, value: self.setIndex( 0, value ) )
	y = property( lambda self: self[ 1 ], lambda self, value: self.setIndex( 1, value ) )
	z = property( lambda self: self[ 2 ], lambda self, value: self.setIndex( 2, value ) )
	w = property( lambda self: self[ 3 ], lambda self, value: self.setIndex( 3, value ) )


class Colour(Vector):
	NAMED_PRESETS = { "active": (0.26, 1, 0.64),
	                  "black": (0, 0, 0),
	                  "white": (1, 1, 1),
	                  "grey": (.5, .5, .5),
	                  "lightgrey": (.7, .7, .7),
	                  "darkgrey": (.25, .25, .25),
	                  "red": (1, 0, 0),
	                  "lightred": (1, .5, 1),
	                  "peach": (1, .5, .5),
	                  "darkred": (.6, 0, 0),
	                  "orange": (1., .5, 0),
	                  "lightorange": (1, .7, .1),
	                  "darkorange": (.7, .25, 0),
	                  "yellow": (1, 1, 0),
	                  "lightyellow": (1, 1, .5),
	                  "darkyellow": (.8,.8,0.),
	                  "green": (0, 1, 0),
	                  "lightgreen": (.4, 1, .2),
	                  "darkgreen": (0, .5, 0),
	                  "blue": (0, 0, 1),
	                  "lightblue": (.4, .55, 1),
	                  "darkblue": (0, 0, .4),
	                  "purple": (.7, 0, 1),
	                  "lightpurple": (.8, .5, 1),
	                  "darkpurple": (.375, 0, .5),
	                  "brown": (.57, .49, .39),
	                  "lightbrown": (.76, .64, .5),
	                  "darkbrown": (.37, .28, .17) }

	NAMED_PRESETS[ 'highlight' ] = NAMED_PRESETS[ 'active' ]
	NAMED_PRESETS[ 'pink' ] = NAMED_PRESETS[ 'lightred' ]

	DEFAULT_COLOUR = NAMED_PRESETS[ 'black' ]
	DEFAULT_ALPHA = 0.7  #alpha=0 is opaque, alpha=1 is transparent

	INDEX_NAMES = 'rgba'
	_EQ_TOLERANCE = 0.1

	_NUM_RE = re.compile( '^[0-9. ]+' )

	def __eq__( self, other, tolerance=_EQ_TOLERANCE ):
		return Vector.__eq__( self, other, tolerance )
	def __ne__( self, other, tolerance=_EQ_TOLERANCE ):
		return Vector.__ne__( self, other, tolerance )
	def __init__( self, colour ):
		'''
		colour can be a combination:
		name alpha  ->  darkred 0.5
		name
		r g b a  ->  1 0 0 0.2
		if r, g, b or a are missing, they're assumed to be 0
		a 4 float, RGBA array is returned
		'''
		if isinstance( colour, basestring ):
			alpha = self.DEFAULT_ALPHA
			toks = colour.lower().split( ' ' )[ :4 ]

			if len( toks ) > 1:
				if toks[ -1 ].isdigit():
					alpha = float( toks[ -1 ] )

			clr = [0,0,0,alpha]
			for n, c in enumerate( self.DEFAULT_COLOUR[ :4 ] ):
				clr[ n ] = c

			clr[ 3 ] = alpha

			if not toks[ 0 ].isdigit():
				try:
					clr = list( self.NAMED_PRESETS[ toks[ 0 ] ] )[ :3 ]
					clr.append( alpha )
				except KeyError: pass
			else:
				for n, t in enumerate( toks ):
					try: clr[ n ] = float( t )
					except ValueError: continue
		else:
			clr = colour

		Vector.__init__( self, clr )
	def darken( self, factor ):
		'''
		returns a colour vector that has been darkened by the appropriate ratio.
		this is basically just a multiply, but the alpha is unaffected
		'''
		darkened = self * factor
		darkened[ 3 ] = self[ 3 ]

		return darkened
	def lighten( self, factor ):
		toWhiteDelta = Colour( (1,1,1,0) ) - self
		toWhiteDelta = toWhiteDelta * factor
		lightened = self + toWhiteDelta
		lightened[ 3 ] = self[ 3 ]

		return lightened
	@classmethod
	def ColourToName( cls, theColour ):
		'''
		given an arbitrary colour, will return the most appropriate name as
		defined in the NAMED_PRESETS class dict
		'''
		if not isinstance( theColour, Colour ):
			theColour = Colour( theColour )

		theColour = Vector( theColour[ :3 ] )  #make sure its a 3 vector
		matches = []
		for name, colour in cls.NAMED_PRESETS.iteritems():
			colour = Vector( colour )
			diff = (colour - theColour).magnitude()
			matches.append( (diff, name) )

		matches.sort()

		return matches[ 0 ][ 1 ]

Color = Colour  #for spelling n00bs


class Axis(int):
	BASE_AXES = 'x', 'y', 'z'
	AXES = ( 'x', 'y', 'z', \
	         '-x', '-y', '-z' )

	def __new__( cls, idx ):
		if isinstance( idx, basestring ):
			return cls.FromName( idx )

		return int.__new__( cls, idx )
	def __neg__( self ):
		return Axis( (self + 3) % 6 )
	@classmethod
	def FromName( cls, name ):
		idx = list( cls.AXES ).index( name.lower().replace( '_', '-' ) )
		return cls( idx )
	@classmethod
	def FromVector( cls, vector ):
		'''
		returns the closest axis to the given vector
		'''
		assert len( cls.BASE_AXES ) >= len( vector )

		listV = list( vector )
		idx, value = 0, listV[ 0 ]
		for n, v in enumerate( listV ):
			if v > value:
				value = v
				idx = n

		return cls( idx )
	def asVector( self ):
		v = Vector( [0, 0, 0] )
		v[ self % 3 ] = 1 if self < 3 else -1

		return v
	def isNegative( self ):
		return self > 2
	def asName( self ):
		return self.AXES[ self ]
	def asCleanName( self ):
		'''
		returns the axis name without a negative regardless
		'''
		return self.AXES[ self ].replace( '-', '' )
	def asEncodedName( self ):
		'''
		returns the axis name, replacing the - with an _
		'''
		return self.asName().replace( '-', '_' )
	def otherAxes( self ):
		'''
		returns the other two axes that aren't this axis
		'''
		allAxes = [ 0, 1, 2 ]
		allAxes.remove( self % 3 )

		return list( map( Axis, allAxes ) )

AX_X, AX_Y, AX_Z = map( Axis, range( 3 ) )


class Quaternion(Vector):
	def __init__( self, x=0, y=0, z=0, w=1 ):
		'''
		initialises a vector from either x,y,z,w args or a Matrix instance
		'''
		if isinstance(x, Matrix):
			#the matrix is assumed to be a valid rotation matrix
			matrix = x
			d1, d2, d3 = matrix.getDiag()
			t = d1 + d2 + d3 + 1.0
			if t > zeroThreshold:
				s = 0.5 / sqrt( t )
				w = 0.25 / s
				x = ( matrix[2][1] - matrix[1][2] )*s
				y = ( matrix[0][2] - matrix[2][0] )*s
				z = ( matrix[1][0] - matrix[0][1] )*s
			else:
				if d1 >= d2 and d1 >= d3:
					s = sqrt( 1.0 + d1 - d2 - d3 ) * 2.0
					x = 0.5 / s
					y = ( matrix[0][1] + matrix[1][0] )/s
					z = ( matrix[0][2] + matrix[2][0] )/s
					w = ( matrix[1][2] + matrix[2][1] )/s
				elif d2 >= d1 and d2 >= d3:
					s = sqrt( 1.0 + d2 - d1 - d3 ) * 2.0
					x = ( matrix[0][1] + matrix[1][0] )/s
					y = 0.5 / s
					z = ( matrix[1][2] + matrix[2][1] )/s
					w = ( matrix[0][2] + matrix[2][0] )/s
				else:
					s = sqrt( 1.0 + d3 - d1 - d2 ) * 2.0
					x = ( matrix[0][2] + matrix[2][0] )/s
					y = ( matrix[1][2] + matrix[2][1] )/s
					z = 0.5 / s
					w = ( matrix[0][1] + matrix[1][0] )/s

		Vector.__init__(self, [x, y, z, w])
	def __mul__( self, other ):
		if isinstance( other, Quaternion ):
			x1, y1, z1, w1 = self
			x2, y2, z2, w2 = other

			newW = w1*w2 - x1*x2 - y1*y2 - z1*z2
			newX = w1*x2 + x1*w2 + y1*z2 - z1*y2
			newY = w1*y2 - x1*z2 + y1*w2 + z1*x2
			newZ = w1*z2 + x1*y2 - y1*x2 + z1*w2

			return self.__class__(newX, newY, newZ, newW)
		elif isinstance( other, (float, int, long) ):
			return self.__class__(self.x*other, self.y*other, self.z*other, self.w*other)
	__rmul__ = __mul__
	def __div__( self, other ):
		assert isinstance( other, (float, int, long) )
		return self.__class__(self.x / other, self.y / other, self.z / other, self.w / other)
	def copy( self ):
		return self.__class__(self)
	@classmethod
	def FromEulerXYZ( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerXYZ(x, y, z, degrees))
	@classmethod
	def FromEulerYZX( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerYZX(x, y, z, degrees))
	@classmethod
	def FromEulerZXY( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerZXY(x, y, z, degrees))
	@classmethod
	def FromEulerXZY( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerXZY(x, y, z, degrees))
	@classmethod
	def FromEulerYXZ( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerYXZ(x, y, z, degrees))
	@classmethod
	def FromEulerZYX( cls, x, y, z, degrees=False ): return cls(Matrix.FromEulerZYX(x, y, z, degrees))
	@classmethod
	def AxisAngle( cls, axis, angle, normalize=False ):
		'''angle is assumed to be in radians'''
		if normalize:
			axis = axis.normalize()

		angle /= 2.0
		newW = cos( angle )
		x, y, z = axis
		s = sin( angle ) / sqrt( x**2 + y**2 + z**2 )

		newX = x * s
		newY = y * s
		newZ = z * s
		new = cls(newX, newY, newZ, newW)
		new = new.normalize()

		return new
	def toAngleAxis( self ):
		'''Return angle (in radians) and rotation axis.
		'''

		nself = self.normalize()

		# Clamp nself.w (since the quat has to be normalized it should
		# be between -1 and 1 anyway, but it might be slightly off due
		# to numerical inaccuracies)
		w = max( min(nself.w, 1.0), -1.0 )

		w = acos( w )
		s = sin( w )
		if s < 1e-12:
			return (0.0, Vector(0, 0, 0))

		return ( 2.0 * w, Vector(nself.x / s, nself.y / s, nself.z / s) )
	def as_tuple( self ):
		return tuple( self )
	def log( self ):
		global zeroThreshold

		b = sqrt(self.x**2 + self.y**2 + self.z**2)
		res = self.__class__()
		if abs( b ) <= zeroThreshold:
			if self.w <= zeroThreshold:
				raise ValueError, "math domain error"

			res.w = math.log( self.w )
		else:
			t = atan2(b, self.w)
			f = t / b
			res.x = f * self.x
			res.y = f * self.y
			res.z = f * self.z
			ct = cos( t )
			if abs( ct ) <= zeroThreshold:
				raise ValueError, "math domain error"

			r = self.w / ct
			if r <= zeroThreshold:
				raise ValueError, "math domain error"

			res.w = math.log( r )

		return res


class Matrix(list):
	'''deals with square matricies'''
	def __init__( self, values=(), size=4 ):
		'''
		initialises a matrix from either an iterable container of values
		or a quaternion.  in the case of a quaternion the matrix is 3x3
		'''
		if isinstance( values, Matrix ):
			size = values.size
			values = values.as_list()
		elif isinstance( values, Quaternion ):
			#NOTE: quaternions result in a 4x4 matrix
			size = 4
			x, y, z, w = values
			xx = 2.0 * x * x
			yy = 2.0 * y * y
			zz = 2.0 * z * z
			xy = 2.0 * x * y
			zw = 2.0 * z * w
			xz = 2.0 * x * z
			yw = 2.0 * y * w
			yz = 2.0 * y * z
			xw = 2.0 * x * w
			row0 = 1.0-yy-zz, xy-zw, xz+yw, 0
			row1 = xy+zw, 1.0-xx-zz, yz-xw, 0
			row2 = xz-yw, yz+xw, 1.0-xx-yy, 0

			values = row0 + row1 + row2 + (0, 0, 0, 1)
		if len(values) > size*size:
			raise MatrixException('too many args: the size of the matrix is %d and %d values were given'%(size,len(values)))
		self.size = size

		for n in range(size):
			row = [ 0 ] * size
			row[ n ] = 1
			self.append( row )

		for n in range( len(values) ):
			self[ n / size ][ n % size ] = values[ n ]
	def __repr__( self ):
		fmt = '%6.3g'
		asStr = []
		for row in self:
			rowStr = []
			for r in row:
				rowStr.append( fmt % r )

			asStr.append( '[%s ]' % ','.join( rowStr ) )

		return '\n'.join( asStr )
	def __str__( self ):
		return self.__repr__()
	def __add__( self, other ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = self[i][j] + other[i][j]

		return new
	def __sub__( self, other ):
		new = self.__class__.Zero(self.size)
		new = self + (other*-1)

		return new
	def __mul__( self, other ):
		new = None
		if isinstance( other, (float, int) ):
			new = self.__class__.Zero(self.size)
			for i in xrange(self.size):
				for j in xrange(self.size):
					new[i][j] = self[i][j] * other

		elif isinstance( other, Vector ):
			return multMatrixVector( self, other )
		else:
			#otherwise assume is a Matrix instance
			new = self.__class__.Zero( self.size )

			cur = self
			if self.size != other.size:
				#if sizes are differnet - shoehorn the smaller matrix into a bigger matrix
				if self.size < other.size:
					cur = self.__class__( self, other.size )
				else:
					other = self.__class__( other, self.size )
			for i in range( self.size ):
				for j in range( self.size ):
					new[i][j] = Vector( cur[i] ) * Vector( other.getCol(j) )

		return new
	def __div__( self, other ):
		return self.__mul__(1.0/other)
	def __eq__( self, other ):
		return self.isEqual(other)
	def __ne__( self, other ):
		return not self.isEqual(other)
	def isEqual( self, other, tolerance=1e-5 ):
		if self.size != other.size:
			return False
		for i in xrange(self.size):
			for j in xrange(self.size):
				if abs( self[i][j] - other[i][j] ) > tolerance:
					return False

		return True
	def copy( self ):
		return self.__class__(self,self.size)
	def crop( self, newSize ):
		new = self.__class__( size=newSize )
		for n in range( newSize ):
			new.setRow( n, self[ n ][ :newSize ] )

		return new
	def expand( self, newSize ):
		new = self.Identity( newSize )
		for i in range( self.size ):
			for j in range( self.size ):
				new[ i ][ j ] = self[ i ][ j ]

		return new
	#some alternative ways to build matrix instances
	@classmethod
	def Zero( cls, size=4 ):
		new = cls([0]*size*size,size)
		return new
	@classmethod
	def Identity( cls, size=4 ):
		rows = [0]*size*size
		for n in xrange(size):
			rows[n+(n*size)] = 1

		return cls(rows,size)
	@classmethod
	def Random( cls, size=4, range=(0,1) ):
		rows = []
		import random
		for n in xrange(size*size):
			rows.append(random.uniform(*range))

		return cls(rows,size)
	@classmethod
	def RotateFromTo( cls, fromVec, toVec, normalize=False ):
		'''Returns a rotation matrix that rotates one vector into another

		The generated rotation matrix will rotate the vector from into
		the vector to. from and to must be unit vectors'''
		e = fromVec*toVec
		f = e.magnitude()

		if f > 1.0-zeroThreshold:
			#from and to vector almost parallel
			fx = abs(fromVec.x)
			fy = abs(fromVec.y)
			fz = abs(fromVec.z)

			if fx < fy:
				if fx < fz: x = Vector(1.0, 0.0, 0.0)
				else: x = Vector(0.0, 0.0, 1.0)
			else:
				if fy < fz: x = Vector(0.0, 1.0, 0.0)
				else: x = Vector(0.0, 0.0, 1.0)

			u = x-fromVec
			v = x-toVec

			c1 = 2.0/(u*u)
			c2 = 2.0/(v*v)
			c3 = c1*c2*u*v

			res = cls(size=3)
			for i in xrange(3):
				for j in xrange(3):
					res[i][j] =  - c1*u[i]*u[j] - c2*v[i]*v[j] + c3*v[i]*u[j]
				res[i][i] += 1.0

			return res
		else:
			#the most common case unless from == to, or from == -to
			v = fromVec^toVec
			h = 1.0/(1.0 + e)
			hvx = h*v.x
			hvz = h*v.z
			hvxy = hvx*v.y
			hvxz = hvx*v.z
			hvyz = hvz*v.y

			row0 = e + hvx*v.x, hvxy - v.z, hvxz + v.y
			row1 = hvxy + v.z, e + h*v.y*v.y,hvyz - v.x
			row2 = hvxz - v.y, hvyz + v.x, e + hvz*v.z

			return cls( row0+row1+row2 )
	@classmethod
	def FromEulerXYZ( cls, x, y, z, degrees=False ):
		if degrees:
			x,y,z = map(math.radians,(x,y,z))

		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cy*cz, cy*sz, -sy
		row1 = sx*sy*cz-cx*sz, sx*sy*sz+cx*cz, sx*cy
		row2 = cx*sy*cz+sx*sz, cx*sy*sz-sx*cz, cx*cy

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerXZY( cls, x, y, z, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		if degrees: x,y,z = map(math.radians,(x,y,z))
		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cy*cz, sy*sx - cy*sz*cx, cy*sz*sx + sy*cx
		row1 = sz, cz*cx, -cz*sx
		row2 = -sy*cz, sy*sz*cx + cy*sx, cy*cx - sy*sz*sx

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerYXZ( cls, x, y, z, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		if degrees: x,y,z = map(math.radians,(x,y,z))
		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cz*cy -sz*sx*sy, -sz*cx, cz*sy + sz*sx*cy
		row1 = sz*cy + cz*sx*sy, cz*cx, sz*sy - cz*sx*cy
		row2 = -cx*sy, sx, cx*cy

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerYZX( cls, x, y, z, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		if degrees: x,y,z = map(math.radians,(x,y,z))
		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cz*cy, -sz, cz*sy
		row1 = cx*sz*cy + sx*sy, cx*cz, cx*sz*sy - sx*cy
		row2 = -sy, sx*cy, cx*cy

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerZXY( cls, x, y, z, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		if degrees: x,y,z = map(math.radians,(x,y,z))
		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cy*cz + sy*sx*sz, sy*sx*cz - cy*sz, sy*cx
		row1 = cx*sz, cx*cz, -sx
		row2 = cy*sx*sz - sy*cz, sy*sz + cy*sx*cz, cy*cx

		return cls( row0+row1+row2, 3 )
	@classmethod
	def FromEulerZYX( cls, x, y, z, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		if degrees: x,y,z = map(math.radians,(x,y,z))
		cx = cos(x)
		sx = sin(x)
		cy = cos(y)
		sy = sin(y)
		cz = cos(z)
		sz = sin(z)

		row0 = cy*cz, -cy*sz, sy
		row1 = sx*sy*cz + cx*sz, cx*cz - sx*sy*sz, -sx*cy
		row2 = sx*sz - cx*sy*cz, cx*sy*sz + sx*cz, cx*cy

		return cls( row0+row1+row2, 3 )
	def getRow( self, row ):
		return self[row]
	def setRow( self, row, newRow ):
		if len(newRow) > self.size: newRow = newRow[:self.size]
		if len(newRow) < self.size:
			newRow.extend( [0] * (self.size-len(newRow)) )

		self[ row ] = newRow

		return newRow
	def getCol( self, col ):
		column = [0]*self.size
		for n in xrange(self.size):
			column[n] = self[n][col]

		return column
	def setCol( self, col, newCol ):
		newColActual = []
		for row, newVal in zip( self, newCol ):
			row[ col ] = newVal
	def getDiag( self ):
		diag = []
		for i in xrange(self.size):
			diag.append( self[i][i] )
		return diag
	def setDiag( self, diag ):
		for i in xrange(self.size):
			self[i][i] = diag[i]
		return diag
	def swapRow( self, nRowA, nRowB ):
		rowA = self.getRow(nRowA)
		rowB = self.getRow(nRowB)
		tmp = rowA
		self.setRow(nRowA,rowB)
		self.setRow(nRowB,tmp)
	def swapCol( self, nColA, nColB ):
		colA = self.getCol(nColA)
		colB = self.getCol(nColB)
		tmp = colA
		self.setCol(nColA,colB)
		self.setCol(nColB,tmp)
	def transpose( self ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = self[j][i]

		return new
	def transpose3by3( self ):
		new = self.copy()
		for i in xrange(3):
			for j in xrange(3):
				new[i][j] = self[j][i]

		return new
	def det( self ):
		'''
		calculates the determinant
		'''
		d = 0
		if self.size <= 0:
			return 1

		if self.size == 2:
			#ad - bc
			a, b, c, d = self.as_list()
			return (a*d) - (b*c)

		for i in range( self.size ):
			sign = (1,-1)[ i % 2 ]
			cofactor = self.cofactor( i, 0 )
			d += sign * self[i][0] * cofactor.det()

		return d
	determinant = det
	def cofactor( self, aI, aJ ):
		cf = self.__class__( size=self.size-1 )
		cfi = 0
		for i in range( self.size ):
			if i == aI:
				continue

			cfj = 0
			for j in range( self.size ):
				if j == aJ:
					continue

				cf[cfi][cfj] = self[i][j]
				cfj += 1
			cfi += 1

		return cf
	minor = cofactor
	def isSingular( self ):
		det = self.det()
		if abs(det) < 1e-6: return True,0
		return False,det
	def isRotation( self ):
		'''rotation matricies have a determinant of 1'''
		return ( abs(self.det()) - 1 < 1e-6 )
	def inverse( self ):
		'''Each element of the inverse is the determinant of its minor
		divided by the determinant of the whole'''
		isSingular,det = self.isSingular()
		if isSingular: return self.copy()

		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				sign = (1,-1)[ (i+j) % 2 ]
				new[i][j] = sign * self.cofactor(i,j).det()

		new /= det

		return new.transpose()
	def adjoint( self ):
		new = self.__class__.Zero(self.size)
		for i in xrange(self.size):
			for j in xrange(self.size):
				new[i][j] = (1,-1)[(i+j)%2] * self.cofactor(i,j).det()

		return new.transpose()
	def ortho( self ):
		'''return a matrix with orthogonal base vectors'''
		x = Vector(self[0][:3])
		y = Vector(self[1][:3])
		z = Vector(self[2][:3])

		xl = x.magnitude()
		xl *= xl
		y = y - ((x*y)/xl)*x
		z = z - ((x*z)/xl)*x

		yl = y.magnitude()
		yl *= yl
		z = z - ((y*z)/yl)*y

		row0 = ( x.x, y.x, z.x )
		row1 = ( x.y, y.y, z.y )
		row2 = ( x.z, y.z, z.z )

		return self.__class__(row0+row1+row2,size=3)
	def decompose( self ):
		'''decomposes the matrix into a rotation and scaling part.
	    returns a tuple (rotation, scaling). the scaling part is given
	    as a 3-tuple and the rotation a Matrix(size=3)'''
		dummy = self.ortho()

		x = dummy[0]
		y = dummy[1]
		z = dummy[2]
		xl = x.magnitude()
		yl = y.magnitude()
		zl = z.magnitude()
		scale = xl,yl,zl

		x/=xl
		y/=yl
		z/=zl
		dummy.setCol(0,x)
		dummy.setCol(1,y)
		dummy.setCol(2,z)
		if dummy.det() < 0:
			dummy.setCol(0,-x)
			scale.x = -scale.x

		return (dummy, scale)
	def getEigenValues( self ):
		m = self

		a, b, c = m[0]
		d, e, f = m[1]
		g, h, i = m[2]

		flA = -1
		flB = a + e + i
		flC = ( d * b + g * c + f * h - a * e - a * i - e * i )
		flD = ( a * e * i - a * f * h - d * b * i + d * c * h + g * b * f - g * c * e )

		return cardanoCubicRoots( flA, flB, flC, flD )
	def get_position( self ):
		return Vector( *self[3][:3] )
	def set_position( self, pos ):
		pos = Vector( pos )
		self[3][:3] = pos

	#the following methods return euler angles of a rotation matrix
	def ToEulerXYZ( self, degrees=False ):
		easy = self[0][2]

		try:
			y = -asin( easy )
		except ValueError:
			z = 0
			if easy == 1:
				y = math.pi / 2.0
				x = z + atan2( self[1][0], self[2][0] )
			else:  #assert easy == -1
				y = -math.pi / 2.0
				x = -z + atan2( -self[1][0], -self[2][0] )
		else:
			cosY = cos( y )
			x = atan2( self[1][2] * cosY, self[2][2] * cosY )
			z = atan2( self[0][1] * cosY, self[0][0] * cosY )

		if degrees:
			return map( math.degrees, (x, y, z) )

		return x, y, z
	def ToEulerXZY( self, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		easy = self[1][0]
		z = asin( easy )
		cosZ = cos( z )

		if easy != 1:
			x = atan2( -self[1][2] * cosZ, self[1][1] * cosZ )
			y = atan2( -self[2][0] * cosZ, self[0][0] * cosZ )
		else:
			pass

		angles = x, y, z

		if degrees:
			return map( math.degrees, angles )

		return angles
	def ToEulerYXZ( self, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		easy = self[2][1]
		x = asin( easy )
		cosX = cos( x )

		if easy != 1:
			y = atan2( -self[2][0] * cosX, self[2][2] * cosX )
			z = atan2( -self[0][1] * cosX, self[1][1] * cosX )
		else:
			pass

		angles = x, y, z

		if degrees:
			return map( math.degrees, angles )

		return angles
	def ToEulerYZX( self, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		easy = self[0][1]
		z = -asin( easy )
		cosZ = cos( z )

		if easy != 1:
			y = atan2( self[0][2] * cosZ, self[0][0] * cosZ )
			x = atan2( self[2][1] * cosZ, self[1][1] * cosZ )
		else: pass

		angles = x, y, z

		if degrees:
			return map( math.degrees, angles )

		return angles
	def ToEulerZXY( self, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		easy = self[1][2]
		x = -asin( easy )
		cosX = cos( x )

		if easy != 1:
			z = atan2( self[1][0] * cosX, self[1][1] * cosX )
			y = atan2( self[0][2] * cosX, self[2][2] * cosX )
		else: pass

		angles = x, y, z

		if degrees:
			return map( math.degrees, angles )

		return angles
	def ToEulerZYX( self, degrees=False ):
		raise NotImplemented( "these aren't correct...  use them at your own peril!" )
		easy = self[0][2]
		y = asin( easy )
		cosY = cos( y )

		if easy != 1:
			x = atan2( -self[1][2] * cosY, self[2][2] * cosY )
			z = atan2( -self[0][1] * cosY, self[0][0] * cosY )
		else: pass

		angles = x, y, z

		if degrees:
			return map( math.degrees, angles )

		return angles
	#some conversion routines
	def as_list( self ):
		list = []
		for i in xrange(self.size):
			list.extend(self[i])

		return list
	def as_tuple( self ):
		return tuple( self.as_list() )


def multMatrixVector( theMatrix, theVector ):
	'''
	multiplies a matrix by a vector - returns a Vector
	'''
	size = theMatrix.size  #square matrices
	size = min( size, len( theVector ) )
	new = theVector.Zero( size )  #init using the actual vector instance just in case its a subclass
	for i in range( size ):
		for j in range( size ):
			new[i] += theMatrix[i][j] * theVector[j]

	return new


def multVectorMatrix( theVector, theMatrix ):
	'''
	mulitplies a vector by a matrix
	'''
	size = theMatrix.size  #square matrices
	size = min( size, len( theVector ) )
	new = theVector.Zero( size )  #init using the actual vector instance just in case its a subclass
	for i in range( size ):
		for j in range( size ):
			new[i] += theVector[j] * theMatrix[j][i]

	return new


def cardanoCubicRoots( flA, flB, flC, flD ):
	'''
	Finds the roots of a Cubic polynomial of the for ax^3 + bx^2 + cx + d = 0
	Returns: True -  3 real roots exists, r0, r1, r2
		False - 1 real root exists, r0, 2 complex roots exist r2, r2
	'''
	flSqrtThree = 1.7320508075688772  #sqrt( 3.0 )

	flF = ( 3.0 * flC / flA - (flB**2) / flA**2 ) / 3.0
	flG = ( 2.0 * (flB**3) / (flA**3) - 9.0 * flB * flC / (flA**2) + 27.0 * flD / flA) / 27.0
	flH = flG**2 / 4.0 + flF**3 / 27.0

	eigenValues = Vector.Zero( 3 )
	if flF == 0 and flG == 0 and flH == 0:
		#3 equal roots
		eigenValues[0] = -( ( flD / flA )**(1/3.0) )  #cube root
		eigenValues[1] = flRoot0
		eigenValues[2] = flRoot1

		return True, eigenValues

	elif flH <= 0:
		#3 real roots
		flI = ( flG**2 / 4.0 - flH )**0.5
		flJ = flI**(1/3.0)
		flK = acos( -( flG / ( 2.0 * flI ) ) )
		flM = cos( flK / 3 )
		flN = flSqrtThree * sin( flK / 3.0 )
		flP = -( flB / ( 3.0 * flA ) )
		eigenValues[0] = 2 * flJ * flM + flP
		eigenValues[1] = -flJ * ( flM + flN ) + flP
		eigenValues[2] = -flJ * ( flM - flN ) + flP

		return True, eigenValues

	#1 Real, 2 Complex Roots
	flR = -( flG / 2 ) + flH**0.5
	flS = flR**(1/3.0)
	flT = -( flG / 2.0 ) - flH**0.5
	flU = flT**(1/3.0)
	flP = -( flB / ( 3.0 * flA ) )
	eigenValues[0] = ( flS + flU ) + flP

	#Return the real part but if it gets here there are complex roots
	eigenValues[1] = -( flS + flU ) / 2.0 + flP
	eigenValues[2] = -( flS + flU ) / 2.0 + flP

	return False, eigenValues


def computeCovariantMatrix( points ):
	centreAccum = Vector.Zero()
	for p in points:
		centreAccum += p

	vMean = centreAccum / len( points )

	nPointCount = len( points )
	if nPointCount <= 0:
		return Matrix.Identity( 3 )

	skewedPointList = [ v-vMean for v in points ]

	m = Matrix( size=3 )
	flPointCount = float( nPointCount )
	for i in range( 3 ):
		for j in range( 3 ):
			flCovariance = 0

			for k in range( nPointCount ):
				flCovariance += skewedPointList[k][i] * skewedPointList[k][j]

			m[i][j] = flCovariance / flPointCount

	return m


def computeSymmetricalEigen( m ):

	def isZero( f ):
		return abs( f ) < 1e-6

	def sign( f ):
		return -1 if f < 0 else 1

	numRows = 3  #len( m )
	numCols = 3  #len( m[0] )

	vEigenValues = Vector.Zero( 3 )
	mEigenVectors = Matrix.Identity( 3 )
	eigenVecRows = 3
	eigenVecCols = 3

	#Perform householder tri-diagonalisation, makes QR iterations better
	#for ( uint k = 0; k < numRows - 2; ++k )
	for k in range( numRows-2 ):
		#Calculate householder vector, store it in the subdiagonal
		#Replacing first value of v (Which is always 1) with beta.
		#For off diagonal symmetric entries only fill in super-diagonal.
		sigma = 0

		x0 = m[k+1][k]
		##for ( uint r = k + 2; r < m.Rows(); ++r )
		for r in range( k+2, numRows ):
			sigma += m[r][k]**2

		if isZero( sigma ):
			m[k+1][k] = 0
		else:
			mu = sqrt( m[k+1][k]**2 + sigma )
			if m[k+1][k] <= 0:
				m[k+1][k] = m[k+1][k] - mu
			else:
				m[k+1][k] = -sigma / ( m[k+1][k] + mu )

			##for ( uint r = k+2; r< m.Rows(); ++r )
			for r in range( k+2, numRows ):
				m[r][k] /= m[k+1][k]

			m[k+1][k] = 2 * ( m[k+1][k]**2 ) / ( sigma + ( m[k+1][k]**2 ) )

		#Set the symmetric entry, needs info from above...
		m[k][k+1] = sqrt( sigma + x0**2 )

		#Update the matrix with the householder transform (Make use of symmetry)...
		#Calculate p/beta, store in d...
		##for ( uint c = k + 1; c < m.Cols(); ++c )
		for c in range( k+1, numCols ):
			vEigenValues[c] = m[c][k + 1]  #First entry of v is 1.
			##for ( uint r = k + 2; r < m.Rows(); ++r )
			for r in range( k+2, numRows ):
				vEigenValues[c] += m[r][k] * m[c][r]

		#Calculate w, replace p with it in d...
		mult = vEigenValues[k + 1]
		##for ( uint r = k + 2; r < m.Rows(); r++ )
		for r in range( k+2, numRows ):
			mult += m[r][k] * vEigenValues[r]

		mult *= ( m[k+1][k]**2 ) / 2.0

		vEigenValues[k + 1] = m[k + 1][k] * vEigenValues[k + 1] - mult
		##for ( uint c = k + 2; c < m.Cols(); ++c )
		for c in range( k+2, numCols ):
			vEigenValues[c] = m[k + 1][k] * vEigenValues[c] - mult * m[c][k]

		#Apply the update - make use of symmetry by only calculating the lower
		#triangular set...
		#First column where first entry of v being 1 matters...
		m[k + 1][k + 1] -= 2.0 * vEigenValues[k + 1]
		##for ( uint r = k + 2; r < m.Rows(); ++r )
		for r in range( k+2, numRows ):
			m[r][k+1] -= m[r][k] * vEigenValues[k+1] + vEigenValues[r]

		#Remainning columns...
		##for ( uint c = k + 2; c < m.Cols(); ++c )
		for c in range( k+2, numCols ):
			##for ( uint r = c; r < m.Rows(); ++r )
			for r in range( c, numRows ):
				m[r][c] -= m[r][k] * vEigenValues[c] + m[c][k] * vEigenValues[r]

		#Do the mirroring...
		##for ( uint r = k + 1; r < m.Rows(); ++r )
		for r in range( k+1, numRows ):
			##for ( uint c = r + 1; c< m.Cols(); ++c )
			for c in range( r+1, numCols ):
				m[r][c] = m[c][r]

	#Use the stored sub-diagonal house-holder vectors to initialise q...
	##for ( int k = static_cast< int >( m.Cols() ) - 3; k >=0; --k )
	kVals = list( reversed( range( numCols-2 ) ) )
	for k in kVals:
		#Arrange for v to start with 1 - avoids special cases...
		beta = m[k+1][k]
		m[k+1][k] = 1

		#Update q, column by column...
		##for ( uint c = static_cast< uint >( k ) + 1; c< mEigenVectors.Cols(); ++c )
		for c in range( k+1, eigenVecCols ):
			#Copy column to tempory storage...
			##for ( uint r = static_cast< uint >( k ) + 1; r< mEigenVectors.Rows(); ++r )
			for r in range( k+1, eigenVecRows ):
				vEigenValues[r] = mEigenVectors[r][c]

			#Update each row in column...
			##for ( uint r = static_cast< uint >( k ) + 1; r < mEigenVectors.Rows(); ++r )
			for r in range( k+1, eigenVecRows ):
				mult = beta * m[r][k]
				##for ( uint i = static_cast< uint >( k ) + 1; i < mEigenVectors.Cols(); ++i )
				for i in range( k+1, eigenVecCols ):
					mEigenVectors[r][c] -= mult * m[i][k] * vEigenValues[i]

	#Now perform QR iterations till we have a diagonalised - at which point it
	#will be the eigenvalues... (Update q as we go.)
	#These parameters decide how many iterations are required...
	epsilon = 1e-6
	max_iters = 64  #Maximum iters per value pair.
	nIterations = 0  #Number of iterations done on current value pair.

	bOk = True  #Return value -set ot false if iters ever reaches max_iters.

	#Range of sub-matrix being processed - start is inclusive, end exclusive.
	start = numRows  #Set to force recalculate.
	end = numRows

	#(Remember that below code ignores the sub-diagonal, as its a mirror of the super diagonal.)
	while True:
		#Move end up as far as possible, finish if done...
		pend = end
		while True:
			em1 = end - 1
			em2 = end - 2
			tol = epsilon * ( abs(m[em2][em2] ) + abs( m[em1][em1] ) )
			if abs( m[em2][em1] ) < tol:
				end -= 1
				if end < 2:
					break
			else:
				break

		if pend == end:
			nIterations += 1
			if nIterations == max_iters:
				bOk = False
				if end == 2:
					break

				nIterations = 0
				end -= 1
				continue
		else:
			if end < 2:
				break

			nIterations = 0

		#If end has caught up with start recalculate it...
		if start + 2 > end:
			start = end - 2
			while start > 0:
				sm1 = start - 1
				tol = epsilon * ( abs( m[sm1][sm1] ) + abs( m[start][start] ) )
				if abs(m[sm1][start] ) >= tol:
					start -= 1
				else:
					break

		#Do the QR step, with lots of juicy optimisation...
		#Calculate eigenvalue of trailing 2x2 matrix...
		em1 = end - 1
		em2 = end - 2
		temp = ( m[em2][em2] - m[em1][em1] ) / 2.0
		div = temp + sign(temp) * sqrt( temp**2 + ( m[em2][em1]**2 ) )
		tev = m[em1][em1] - ( m[em2][em1]**2 ) / div

		#Calculate and apply relevant sequence of givens transforms to
		#flow the numbers down the super/sub-diagonals...
		x = m[start][start] - tev
		z = m[start][start+1]

		##for ( int k = start; ; ++k )
		for k in range( start, 1000000 ):
			#Calculate givens transform...
			gc = 1
			gs = 0
			if not isZero( z ):
				if abs( z ) > abs( x ):
					r = -x / z
					gs = 1.0 / sqrt( 1 + r**2 )
					gc = gs * r
				else:
					r = -z / x
					gc = 1 / sqrt( 1 + r**2 )
					gs = gc * r

			gcc = gc**2
			gss = gs**2


			#Update matrix q (Post multiply)...
			##for ( uint r = 0; r < mEigenVectors.Rows(); ++r )
			for r in range( eigenVecRows ):
				ck  = mEigenVectors[r][k]
				ck1 = mEigenVectors[r][k+1]
				mEigenVectors[r][k]   = gc * ck - gs * ck1
				mEigenVectors[r][k+1] = gs * ck + gc * ck1


			#Update matrix a...
			#Conditional on not being at start of range...
			if k != start:
				m[k-1][k] = gc * x - gs * z

			#Non-conditional...
			e = m[k][k]
			f = m[k+1][k+1]
			i = m[k][k+1]

			m[k][k] = gcc * e + gss * f - 2 * gc * gs * i
			m[k+1][k+1] = gss * e + gcc * f + 2 * gc * gs * i
			m[k][k+1] = gc * gs * ( e - f ) + ( gcc - gss ) * i
			x = m[k][k+1]

			#Conditional on not being at end of range...
			if k != end - 2:
				z = -gs * m[k+1][k+2]
				m[k+1][k+2] *= gc
			else:
				break


	#Fill in the diagonal...
	##for ( uint i = 0; i < vEigenValues.Size(); ++i )
	for i in range( len( vEigenValues ) ):
		vEigenValues[i] = m[i][i]

	return mEigenVectors, vEigenValues, bOk


def closestPointOnLineTo( linePt1List, linePt2List, givenPointList ):
	"""
	given 3 float lists, return closest point in space (as a float list) from the givenPoint to the line between the first 2 args
	"""


	vA = Vector( linePt1List )
	vB = Vector( linePt2List )
	vPoint = Vector( givenPointList )

	vABDir = vB - vA
	vABDirNrm = vABDir.normalize()

	origDistance = vABDir.get_magnitude()

	v1 = vPoint - vA
	t = v1.dot( vABDirNrm )

	if t <= 0.0:
		return linePt1List
	elif t >= origDistance:
		return linePt2List

	v3 = vABDirNrm * t
	vClosestPoint = vA + v3

	return ( vClosestPoint.x, vClosestPoint.y, vClosestPoint.z )


def mirrorEulerRotation( eulerRotation, axis=AX_X, degrees=True ):
	rots = Matrix.FromEulerXYZ( degrees=degrees, *eulerRotation )
	x, y, z = map( Vector, rots )

	idxA, idxB = axis.otherAxes()
	x[ idxA ] = -x[ idxA ]
	x[ idxB ] = -x[ idxB ]

	y[ idxA ] = -y[ idxA ]
	y[ idxB ] = -y[ idxB ]

	z[ idxA ] = -z[ idxA ]
	z[ idxB ] = -z[ idxB ]

	mirroredRotMatrix = Matrix( list(x) + list(y) + list(z), 3 )

	return mirroredRotMatrix.ToEulerXYZ( useDegrees )


#end

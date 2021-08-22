"""
Copyright (c) 2014-2015 Gen Del Raye
Copyright (c) 2015 Ryan Vennell

This is a derivative, forked from the original work by:
Gen Del Raye <gdelraye@hawaii.edu> and located at:
https://pypi.python.org/pypi/LatLon

Licensed under the GPLv3: http://www.gnu.org/licenses/gpl-3.0.html
"""
import math
import re
import pyproj
import warnings
import abc

'''
Methods for representing geographic coordinates (latitude and longitude)
Features:
    Convert lat/lon strings from any format into a LatLon object
    Automatically store decimal degrees, decimal minutes, and degree, minute, second
      information in a LatLon object
    Output lat/lon information into a formatted string
    Project lat/lon coordinates into some other proj projection
    Calculate distances between lat/lon pairs using either the FAI or WGS84 approximation
Written July 22, 2014
Author: Gen Del Raye
'''
# TODO: Write methods to convert -180 to 180 longitudes to 0 to 360 and vice versa

def compare(a, b):
    return (a > b) - (a < b)

class GeoCoord:
    '''
    Abstract class representing geographic coordinates (i.e. latitude or longitude)
    Not meant to be used directly - access through Subclasses Latitude() and Longitude()
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, degree = 0, minute = 0, second = 0):
        '''
        Initialize a GeoCoord object
        Inputs:
            degree (scalar) - integer or decimal degrees. If decimal degrees are given (e.g. 5.83),
              the fractional values (0.83) will be added to the minute and second variables.
            minute (scalar) - integer or decimal minutes. If decimal minutes are given (e.g. 49.17),
              the fractional values (0.17) will be added to the second variable.
            second (scalar) - decimal minutes.
        '''
        self.degree = float(degree)
        self.minute = float(minute)
        self.second = float(second)
        self._update() # Clean up each variable and make them consistent

    def set_minute(self, minute):
        self.minute = float(minute)

    def set_second(self, second):
        self.second = float(second)

    def set_degree(self, degree):
        self.degree = float(degree)

    @staticmethod
    def _calc_decimaldegree(degree, minute, second):
        '''
        Calculate decimal degree form degree, minute, second
        '''
        return degree + minute/60. + second/3600.

    @staticmethod
    def _calc_degreeminutes(decimal_degree):
        '''
        Calculate degree, minute second from decimal degree
        '''
        sign = compare(decimal_degree, 0) # Store whether the coordinate is negative or positive
        decimal_degree = abs(decimal_degree)
        degree = decimal_degree//1 # Truncate degree to be an integer
        decimal_minute = (decimal_degree - degree)*60. # Calculate the decimal minutes
        minute = decimal_minute//1 # Truncate minute to be an integer
        second = (decimal_minute - minute)*60. # Calculate the decimal seconds
        # Finally, re-impose the appropriate sign
        degree = degree*sign
        minute = minute*sign
        second = second*sign
        return (degree, minute, decimal_minute, second)

    def _update(self):
        '''
        Given degree, minute, and second information, clean up the variables and make them
        consistent (for example, if minutes > 60, add extra to degrees, or if degrees is
        a decimal, add extra to minutes).
        '''
        self.decimal_degree = self._calc_decimaldegree(self.degree, self.minute, self.second)
        self.degree, self.minute, self.decimal_minute, self.second = self._calc_degreeminutes(self.decimal_degree)

    @abc.abstractmethod
    def get_hemisphere(self):
        '''
        Dummy method, used in child classes such as Latitude and Longitude
        '''
        pass

    @abc.abstractmethod
    def set_hemisphere(self):
        '''
        Dummy method, used in child classes such as Latitude and Longitude
        '''
        pass

    def to_string(self, format_str):
        '''
        Output lat, lon coordinates as string in chosen format
        Inputs:
            format (str) - A string of the form A%B%C where A, B and C are identifiers.
              Unknown identifiers (e.g. ' ', ', ' or '_' will be inserted as separators
              in a position corresponding to the position in format.
        Examples:
            >> palmyra = LatLon(5.8833, -162.0833)
            >> palmyra.to_string('D') # Degree decimal output
            ('5.8833', '-162.0833')
            >> palmyra.to_string('H% %D')
            ('N 5.8833', 'W 162.0833')
            >> palmyra.to_string('d%_%M')
            ('5_52.998', '-162_4.998')
        '''
        format2value = {'H': self.get_hemisphere(),
                        'M': abs(self.decimal_minute),
                        'm': int(abs(self.minute)),
                        'd': int(self.degree),
                        'D': self.decimal_degree,
                        'S': abs(self.second)}
        format_elements = format_str.split('%')
        coord_list = [str(format2value.get(element, element)) for element in format_elements]
        coord_str = ''.join(coord_list)
        if 'H' in format_elements: # No negative values when hemispheres are indicated
            coord_str = coord_str.replace('-', '')
        return coord_str

    def __cmp__(self, other):
        return compare(self.decimal_degree, other.decimal_degree)

    def __neg__(self):
        return GeoCoord(-self.decimal_degree)

    def __pos__(self):
        return GeoCoord(self.decimal_degree)

    def __abs__(self):
        self.__pos__()
        return self

    def __add__(self, other):
        # other is a scalar
        return GeoCoord(self.decimal_degree + other)

    def __iadd__(self, other):
        # other is a scalar
        return self.__add__(other)

    def __radd__(self, other):
        # other is a scalar
        return self.__add__(other)

    def __sub__(self, other):
        # other is a scalar
        return self.__add__(-other)

    def __isub__(self, other):
        # other is a scalar
        return self.__sub__(other)

    def __rsub__(self, other):
        # other is a scalar
        return self.__sub__(other)

    def __floor__(self):
        return GeoCoord(math.floor(self.decimal_degree))

    def __round__(self):
        return GeoCoord(round(self.decimal_degree))

    def __ceil__(self):
        return GeoCoord(math.ceil(self.decimal_degree))

    def __int__(self):
        return self.degree

    def __float__(self):
        return self.decimal_degree

    def __str__(self):
        return str(self.decimal_degree)

    def __repr__(self):
        return self.__str__()

    def type(self):
        '''
        Identifies the object type
        '''
        return 'GeoCoord'

class Latitude(GeoCoord):
    '''
    Coordinate object specific for latitude coordinates
    '''
    def get_hemisphere(self):
        '''
        Returns the hemisphere identifier for the current coordinate
        '''
        if self.decimal_degree < 0: return 'S'
        else: return 'N'

    def set_hemisphere(self, hemi_str):
        '''
        Given a hemisphere identifier, set the sign of the coordinate to match that hemisphere
        '''
        if hemi_str == 'S':
            self.degree = abs(self.degree)*-1
            self.minute = abs(self.minute)*-1
            self.second = abs(self.second)*-1
            self._update()
        elif hemi_str == 'N':
            self.degree = abs(self.degree)
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update()
        else:
            raise ValueError('Hemisphere identifier for latitudes must be N or S')

    def __repr__(self):
        return 'Latitude %s' %(self.__str__())

class Longitude(GeoCoord):
    '''
    Coordinate object specific for longitude coordinates
    Langitudes outside the range -180 to 180 (i.e. those reported in the range 0 to 360) will
    automatically be converted to 0 to 360 to ensure that all operations such as hemisphere
    assignment work as expected. To report in the range 0 to 360, use method range360()
    '''
    def __init__(self, degree = 0, minute = 0, second = 0):
        super(Longitude, self).__init__(degree, minute, second) # Initialize the GeoCoord
        decimal_degree = self.range180() # Make sure that longitudes are reported in the range -180 to 180
        self.degree, self.minute, self.decimal_minute, self.second = self._calc_degreeminutes(decimal_degree)
        self._update()

    def range180(self):
        '''
        Report longitudes using the range -180 to 180.
        '''
        return ((self.decimal_degree + 180)%360) - 180


    def range360(self):
        '''
        Report longitudes using the range 0 to 360
        '''
        return (self.decimal_degree + 360)%360

    def get_hemisphere(self):
        '''
        Returns the hemisphere identifier for the current coordinate
        '''
        if self.decimal_degree < 0: return 'W'
        else: return 'E'

    def set_hemisphere(self, hemi_str):
        '''
        Given a hemisphere identifier, set the sign of the coordinate to match that hemisphere
        '''
        if hemi_str == 'W':
            self.degree = abs(self.degree)*-1
            self.minute = abs(self.minute)*-1
            self.second = abs(self.second)*-1
            self._update()
        elif hemi_str == 'E':
            self.degree = abs(self.degree)
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update()
        else:
            raise ValueError('Hemisphere identifier for longitudes must be E or W')

    def __repr__(self):
        return 'Longitude %s' %(self.__str__())

def string2geocoord(coord_str, coord_class, format_str = 'D'):
    '''
    Create a GeoCoord object (e.g. Latitude or Longitude) from a string.
    Inputs:
        coord_str (str) - a string representation of a geographic coordinate (e.g. '5.083 N'). Each
          section of the string must be separated by some kind of a separator character ('5.083N' is
          invalid).
        coord_class (class) - a class inheriting from GeoCoord that includes a set_hemisphere method.
          Can be either Latitude or Longitude
        format_str (str) - a string representation of the sections of coord_str. Possible letter values
        correspond to the keys of the dictionary format2value, where
              'H' is a hemisphere identifier (e.g. N, S, E or W)
              'D' is a coordinate in decimal degrees notation
              'd' is a coordinate in degrees notation
              'M' is a coordinate in decimal minutes notaion
              'm' is a coordinate in minutes notation
              'S' is a coordinate in seconds notation
              Any other characters (e.g. ' ' or ', ') will be treated as a separator between the above components.
          All components should be separated by the '%' character. For example, if the coord_str is
          '5, 52, 59.88_N', the format_str would be 'd%, %m%, %S%_%H'
    Returns:
        GeoCoord object initialized with the coordinate information from coord_str
    '''
    new_coord = coord_class()
    # Dictionary of functions for setting variables in the coordinate class:
    format2value = {'H': new_coord.set_hemisphere,
                    'M': new_coord.set_minute,
                    'm': new_coord.set_minute,
                    'd': new_coord.set_degree,
                    'D': new_coord.set_degree,
                    'S': new_coord.set_second}
    if format_str[0] == 'H':
        ''' Having the hemisphere identifier at the beginning is problematic for ensuring that
        the final coordinate value will be negative. Instead, change the identifier and the
        format string so that the hemisphere is identified at the end:'''
        new_coord_start = re.search('\d', coord_str).start() # Find the beginning of the coordinate
        new_format_start = re.search('[a-gi-zA-GI-Z]', format_str).start() # Find the first non-hemisphere identifier
        format_str = '% %'.join((format_str[new_format_start:], format_str[0])) # Move hemisphere identifier to the back
        coord_str = ' '.join((coord_str[new_coord_start:], coord_str[0])) # Move hemisphere identifier to the back
    format_elements = format_str.split('%')
    separators = [sep for sep in format_elements if sep not in format2value.keys()] # E.g. ' ', '_' or ', ' characters
    separators.append('%') # Dummy separator for the final part of the coord_str
    formatters = [form for form in format_elements if form in format2value.keys()] # E.g. 'D', 'm', or 'S' characters
    for form, sep in zip(formatters, separators):
        coord_elements = coord_str.split(sep)
        format2value[form](coord_elements[0]) # Set the coordinate variable (e.g. 'self.degree' with the coordinate substring (e.g. '5')
        coord_str = sep.join(coord_elements[1:]) # Get rid of parts of the substring that have already been done
    new_coord._update() # Change all of the variables in the coordinate class so they are consistent with each other
    return new_coord

class LatLon:
    '''
    Object representing lat/lon pairs
    '''
    def __init__(self, lat, lon, name = None):
        '''
        Input:
            lat (class instance or scalar) - an instance of class Latitude or a scalar. A Latitude object
              can be instantiated directly in the __init__ call for example by calling LatLon(Latitude(5.8),
              Longitude(162.5)). If lat is specified as a scalar, the scalar will be assumed to be in
              decimal degrees.
            lon (class instance or scalar) - an instance of class Longitude or a scalar. If lat is
              specified as a scalar, the scalar will be assumed to be in decimal degrees.
            name (str) - an identifier
        '''
        try:
            if lat.type() == 'GeoCoord':
                self.lat = lat
            else:
                raise AttributeError
        except AttributeError:
            self.lat = Latitude(lat)
        try:
            if lon.type() == 'GeoCoord':
                self.lon = lon
            else:
                raise AttributeError
        except AttributeError:
            self.lon = Longitude(lon)
        self.name = name

    def project(self, projection):
        '''
        Return coordinates transformed to a given projection
        Projection should be a basemap or pyproj projection object or similar
        '''
        x, y = projection(self.lon.decimal_degree, self.lat.decimal_degree)
        return (x, y)

    def complex(self):
        '''
        Return lat/lon pairs as complex coordinates
        '''
        return self.lat.decimal_degree + 1j * self.lon.decimal_degree

    def _pyproj_inv(self, other, ellipse = 'WGS84'):
        '''
        Perform Pyproj's inv operation on two LatLon objects
        Returns the initial heading and reverse heading in degrees, and the distance
        in km.
        '''
        lat1, lon1 = self.lat.decimal_degree, self.lon.decimal_degree
        lat2, lon2 = other.lat.decimal_degree, other.lon.decimal_degree
        g = pyproj.Geod(ellps = ellipse)
        heading_initial, heading_reverse, distance = g.inv(lon1, lat1, lon2, lat2, radians = False)
        distance = distance/1000.0
        if heading_initial == 0.0: # Reverse heading not well handled for coordinates that are directly south
            heading_reverse = 180.0
        return {'heading_initial': heading_initial, 'heading_reverse': heading_reverse, 'distance': distance}

    def heading_initial(self, other, **kwargs):
        '''
        Returns initial bearing between two LatLon objects in degrees using pyproj.
        Assumes the WGS84 ellipsoid by default. Choose ellipse = 'sphere'
        for the FAI ellipsoid.
        '''
        return self._pyproj_inv(other, **kwargs)['heading_initial']

    def heading_reverse(self, other, **kwargs):
        '''
        Returns reverse bearing between two LatLon objects in degrees using pyproj.
        Assumes the WGS84 ellipsoid by default. Choose ellipse = 'sphere'
        for the FAI ellipsoid.
        '''
        return self._pyproj_inv(other, **kwargs)['heading_reverse']

    def distance(self, other, **kwargs):
        '''
        Returns great circle distance between two LatLon objects in km using pyproj.
        Assumes the WGS84 ellipsoid by default. Choose ellipse = 'sphere'
        for the FAI ellipsoid.
        '''
        return self._pyproj_inv(other, **kwargs)['distance']

    def distance_sphere(self, other, radius = 6371.0):
        '''
        -- Deprecated in v0.70. Use distance(other, ellipse = 'sphere') instead --

        Returns great circle distance between two lat/lon coordinates on a sphere
        using the Haversine formula. The default radius corresponds to the FAI sphere
        with units in km.
        '''
        warnings.warn("Deprecated in v0.70. Use distance(other, ellipse = 'sphere') instead",
                      DeprecationWarning)
        lat1, lon1 = self.lat.decimal_degree, self.lon.decimal_degree
        lat2, lon2 = other.lat.decimal_degree, other.lon.decimal_degree
        pi = math.pi/180.
        # phi is 90 - latitude
        phi1 = (90. - lat1)*pi
        phi2 = (90. - lat2)*pi
        # theta is longitude
        theta1 = lon1*pi
        theta2 = lon2 *pi
        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
               math.cos(phi1)*math.cos(phi2))
        arc = math.acos(cos)
        return arc*radius

    def offset(self, heading_initial, distance, ellipse = 'WGS84'):
        '''
        Offset a LatLon object by a heading (in degrees) and distance (in km)
        to return a new LatLon object
        '''
        lat1, lon1 = self.lat.decimal_degree, self.lon.decimal_degree
        g = pyproj.Geod(ellps = ellipse)
        distance = distance * 1000 # Convert km to meters
        lon2, lat2, back_bearing = g.fwd(lon1, lat1, heading_initial, distance, radians = False)
        return LatLon(Latitude(lat2), Longitude(lon2))

    def to_string(self, formatter = 'D'):
        '''
        Return string representation of lat and lon as a 2-element tuple
        using the format specified by formatter
        '''
        return (self.lat.to_string(formatter), self.lon.to_string(formatter))

    def _sub_vector(self, other):
        '''
        Called when subtracting a GeoVector object from self
        '''
        heading, distance = other()
        heading = (heading + 180)%360 # Flip heading
        new_latlon = LatLon(self.lat, self.lon) # Copy current position
        return new_latlon.offset(heading, distance) # Offset position by GeoVector

    def _sub_latlon(self, other):
        '''
        Called when subtracting a LatLon object from self
        '''
        inv = self._pyproj_inv(other)
        heading = inv['heading_reverse']
        distance = inv['distance']
        return GeoVector(initial_heading = heading, distance = distance)

    def almost_equal(self, other, e = 0.000001):
        '''
        Sometimes required for comparing LatLon coordinates if float error has
        occurred. Determine if self and other (another LatLon coordinate) are
        equal to within e km of each other. The default (e = 0.000001) will return
        True if self and other are less than 1 mm apart in distance.
        '''
        return (self - other).magnitude < e

    def __eq__(self, other):
        # other is a LatLon object
        if self.lat == other.lat and self.lon == other.lon:
            return True
        else:
            return False

    def __ne__(self, other):
        # other is a LatLon object
        return not self.__eq__(other)

    def __add__(self, other):
        # other is a GeoVector object
        heading, distance = other()
        new_latlon = LatLon(self.lat, self.lon)
        return new_latlon.offset(heading, distance)

    def __iadd__(self, other):
        # other is a GeoVector object
        return self.__add__(other)

    def __radd__(self, other):
        # other is a GeoVector object
        return self.__add__(other)

    def __sub__(self, other):
        # if other is a GeoVector, will return LatLon object
        # if other is a LatLon, will return GeoVector object
        object_operator = {'GeoVector': self._sub_vector,
                           'LatLon': self._sub_latlon}
        return object_operator[other.type()](other)

    def __isub__(self, other):
        # other is a GeoVector object
        return self.__sub__(other)

    def __rsub__(self, other):
        # other is a GeoVector object
        return self.__sub__(other)

    def __str__(self):
        return '%s, %s' %(self.lat.__str__(), self.lon.__str__())

    def __repr__(self):
        return '%s, %s' %(self.lat.__repr__(), self.lon.__repr__())

    def __complex__(self):
        return self.complex()

    def type(self):
        '''
        Identifies the object type
        '''
        return 'LatLon'

def string2latlon(lat_str, lon_str, format_str):
    '''
    Create a LatLon object from a pair of strings.
    Inputs:
        lat_str (str) - string representation of a latitude (e.g. '5 52 59.88 N')
        lon_str (str) - string representation of a longitude (e.g. '162 4 59.88 W')
        format_str (str) - format in which the coordinate strings are given (e.g.
          for the above examples this would be 'd% %m% %S% %H'). See function
          string2geocoord for a detailed explanation on how to specify formats.
    Returns:
        A LatLon object initialized with coordinate data from lat_str and lon_str
    '''
    lat = string2geocoord(lat_str, Latitude, format_str)
    lon = string2geocoord(lon_str, Longitude, format_str)
    new_latlon = LatLon(lat = lat, lon = lon)
    return new_latlon

class GeoVector:
    '''
    Object representing the distance and heading between two lat/lon coordinates
    Can be created by:
        1. Passing dx and dy arguments
        2. Passing initial_heading and distance keyword arguments
        3. Subtracting two LatLon objects
    '''
    def __init__(self, dx = None, dy = None, initial_heading = None, distance = None):
        '''
        Create a GeoVector object
        Inputs:
            dx (scalar) - the zonal component of a vector in km
            dy (scalar) - the meridional component of a vector in km
            initial_heading (scalar) - the initial heading of the vector in degrees
            distance (scalar) - the magnitude of the vector in km
        '''
        if dx == None and dy == None: # If only initial_heading and distance are given
            self.heading = initial_heading
            theta = self._angle_or_heading(self.heading) # Convert heading to angle
            theta_rad = math.radians(theta)
            self.magnitude = distance
            self.dx = self.magnitude * math.cos(theta_rad)
            self.dy = self.magnitude * math.sin(theta_rad)
        elif initial_heading == None and distance == None: # If only dx and dy are given
            self.dx = dx
            self.dy = dy
            self._update()
        else:
            raise NameError('Class GeoVector requires two arguments (dx and dy or initial_heading and distance)')

    def __call__(self):
        return self.heading, self.magnitude

    def _angle_or_heading(self, angle_or_heading):
        '''
        Convert angle degrees (i.e. starting at coordinates (1, 0) or
        due East and going clockwise to 360) into heading (i.e. starting
        at coordinates (0, 1) or due North and going counterclockwise to
        360) or vice versa.
        '''
        heading_or_angle = (90 - angle_or_heading)%360
        return heading_or_angle

    def _update(self):
        '''
        Calculate heading and distance from dx and dy
        '''
        try:
            theta_radians = math.atan(float(self.dy)/self.dx)
        except ZeroDivisionError:
            if self.dy > 0: theta_radians = 0.5*math.pi
            elif self.dy < 0: theta_radians = 1.5*math.pi
            self.magnitude = self.dy
        else:
            self.magnitude = 1./(math.cos(theta_radians))*self.dx
        theta = math.degrees(theta_radians)
        self.heading = self._angle_or_heading(theta) # Convert angle to heading

    def almost_equals(self, other, e = 0.000001):
        '''
        Sometimes required for comparing GeoVectors if float error has
        occurred. Determine if self and other (another GeoVector) are
        equal to within e km of each other in dx and dy. The default
        (e = 0.000001) will return True if self and other are less than
        1 mm apart in distance.
        '''
        return abs(self.dx - other.dx) < e and abs(self.dy - other.dy) < e

    def __neg__(self):
        return GeoVector(-self.dx, -self.dy)

    def __add__(self, other):
        # other is a GeoVector object
        return GeoVector(self.dx + other.dx, self.dy + other.dy)

    def __iadd__(self, other):
        # other is a GeoVector object
        return self.__add__(other)

    def __radd__(self, other):
        # other is a GeoVector object
        return self.__add__(other)

    def __sub__(self, other):
        # other is a GeoVector object
        return self.__add__(-other)

    def __isub__(self, other):
        # other is a GeoVector object
        return self.__sub__(other)

    def __rsub__(self, other):
        # other is a GeoVector object
        return self.__sub__(other)

    def __cmp__(self, other):
        return compare(self.magnitude, other.magnitude)

    def __pos__(self):
        return GeoVector(self.dx, self.dy)

    def __abs__(self):
        return self.__pos__()

    def __mul__(self, other):
        # other is a scalar
        return GeoVector(initial_heading = self.heading, distance = self.magnitude * other)

    def __imul__(self, other):
        # other is a scalar
        return self.__mul__(other)

    def __rmul__(self, other):
        # other is a scalar
        return self.__mul__(other)

    def __div__(self, other):
        # other is a scalar
        return GeoVector(initial_heading = self.heading, distance = self.magnitude / other)

    def __idiv__(self, other):
        # other is a scalar
        return self.__div__(other)

    def __rdiv__(self, other):
        # other is a scalar
        return self.__div__(other)

    def __str__(self):
        return '%s, %s' %(self.heading, self.magnitude)

    def __repr__(self):
        return 'Heading %s, Distance %s' %(self.heading, self.magnitude)

    def type(self):
        '''
        Identifies the object type
        '''
        return 'GeoVector'

def demonstration():
    palmyra = LatLon(Latitude(5.8833), Longitude(-162.0833)) # Try instantiating Latitude and Longitude objects in call
    palmyra # Returns 'Latitude 5.8833, Longitude -162.0833'
    palmyra = LatLon(5.8833, -162.0833) # Or even simpler - initialize from two scalars expressing decimal degrees
    print(str(palmyra)) # Returns '5.8833, -162.0833'
    palmyra = LatLon(Latitude(degree = 5, minute = 52, second = 59.88), Longitude(degree = -162, minute = -4.998)) # or more complicated!
    print(palmyra.to_string('d% %m% %S% %H')) # Print coordinates to degree minute second (returns ('5 52 59.88 N', '162 4 59.88 W'))
    palmyra = string2latlon('5 52 59.88 N', '162 4 59.88 W', 'd% %m% %S% %H') # Initialize from more complex string
    print(palmyra.to_string('d%_%M')) # Print coordinates as degree minutes separated by underscore (returns ('5_52.998', '-162_4.998'))
    palmyra = string2latlon('N 5, 52.998', 'W 162, 4.998', 'H% %d%, %M') # An alternative complex string
    print(palmyra.to_string('D')) # Print coordinate to decimal degrees (returns ('5.8833', '-162.0833'))
    honolulu = LatLon(Latitude(21.3), Longitude(-157.8167))
    print(palmyra.distance(honolulu, ellipse = 'sphere')) # FAI distance is 1774.77188181 km
    distance = palmyra.distance(honolulu) # WGS84 distance is 1766.69130376 km
    print(distance)
    initial_heading = palmyra.heading_initial(honolulu) # Initial heading to Honolulu on WGS84 ellipsoid
    print(initial_heading)
    hnl = palmyra.offset(initial_heading, distance) # Reconstruct lat/lon for Honolulu based on offset from Palmyra
    print(hnl.to_string('D')) # Coordinates of Honolulu are latitude 21.3, longitude -157.8167
    vector = (honolulu - palmyra) * 2 # A GeoVector with heading equal to the vector between palmyra and honolulu, but 2x the magnitude
    print(vector) # Print heading and magnitude
    print(palmyra + (vector/2.0)) # Recreate the coordinates of Honolulu by adding half of vector to palmyra
    print('Finished running demonstration!')

if __name__ == '__main__':
    demonstration()

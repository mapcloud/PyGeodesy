
# -*- coding: utf-8 -*-

'''Trigonometric spherical geodetic (lat-longitude) class L{LatLon}
and functions L{intersection} and L{meanOf}.

Python implementation of geodetic (lat-/longitude) methods using
spherical trigonometry.  Transcribed from JavaScript originals by
I{(C) Chris Veness 2011-2016} published under the same MIT Licence**,
see U{http://www.movable-type.co.uk/scripts/latlong.html}.

@newfield example: Example, Examples
'''

from datum import R_M
from sphericalBase import LatLonSphericalBase
from utils import EPS, EPS1, PI, PI2, PI_2, \
                  degrees90, degrees180, degrees360, \
                  favg, fsum, hsin, map1, radians, wrapPI
from vector3d import Vector3d, sumOf

from math import acos, asin, atan2, cos, hypot, sin, sqrt

# all public contants, classes and functions
__all__ = ('LatLon',  # classes
           'intersection', 'meanOf')  # functions
__version__ = '17.03.13'


class LatLon(LatLonSphericalBase):
    '''New point on spherical model earth model.

       @example:

       >>> p = LatLon(52.205, 0.119)  # height=0
    '''

    _v3d = None  # cache Vector3d

    def _update(self, updated):
        '''(INTERNAL) Clear caches if updated.
        '''
        if updated:  # reset caches
            self._v3d = None
            LatLonSphericalBase._update(self, updated)

    def bearingTo(self, other):
        '''Computes the initial bearing (aka forward azimuth) from
           this to an other point.

           @param other: The other point (L{LatLon}).

           @return: Initial bearing (compass degrees).

           @raise TypeError: The other point is not L{LatLon}.

           @example:

           >>> p1 = LatLon(52.205, 0.119)
           >>> p2 = LatLon(48.857, 2.351)
           >>> b = p1.bearingTo(p2)  # 156.2
        '''
        self.others(other)

        a1, b1 = self.to2ab()
        a2, b2 = other.to2ab()

        db = b2 - b1

        ca1, ca2, cdb = map1(cos, a1, a2, db)
        sa1, sa2, sdb = map1(sin, a1, a2, db)

        # see http://mathforum.org/library/drmath/view/55417.html
        x = ca1 * sa2 - sa1 * ca2 * cdb
        y = sdb * ca2

        return degrees360(atan2(y, x))

    def crossingParallels(self, other, lat):
        '''Return the pair of meridians at which a great circle defined
           by this and an other point crosses the given latitude.

           @param other: The other point defining great circle (L{LatLon}).
           @param lat: Latitude at the crossing (degrees).

           @return: 2-Tuple (lon1, lon2) in (degrees180) or None if the
                    great circle doesn't reach the given latitude.
        '''
        self.others(other)

        a1, b1 = self.to2ab()
        a2, b2 = other.to2ab()

        a, db = radians(lat), (b2 - b1)

        ca, ca1, ca2, cdb = map1(cos, a, a1, a2, db)
        sa, sa1, sa2, sdb = map1(sin, a, a1, a2, db)

        x = sa1 * ca2 * ca * sdb
        y = sa1 * ca2 * ca * cdb - ca1 * sa2 * ca
        z = ca1 * ca2 * sa * sdb

        h = hypot(x, y)
        if abs(z) > h:
            return None  # great circle doesn't reach latitude

        m = atan2(-y, x) + b1  # longitude at max latitude
        d = acos(z / h)  # delta longitude to intersections

        return degrees180(m - d), degrees180(m + d)

    def crossTrackDistanceTo(self, start, end, radius=R_M):
        '''Returns (signed) distance from this point to great circle
           defined by a start and end point.

           @param start: Start point of great circle path (L{LatLon}).
           @param end: End point of great circle path (L{LatLon}).
           @keyword radius: Mean earth radius (meter).

           @return: Distance to great circle (negative if to the
                    left or positive if to the right of the path).

           @raise TypeError: The start or end point is not L{LatLon}.

           @example:

           >>> p = LatLon(53.2611, -0.7972)

           >>> s = LatLon(53.3206, -1.7297)
           >>> e = LatLon(53.1887, 0.1334)
           >>> d = p.crossTrackDistanceTo(s, e)  # -307.5
        '''
        self.others(start, name='start')
        self.others(end, name='end')

        r = start.distanceTo(self, radius) / float(radius)
        b = radians(start.bearingTo(self))
        e = radians(start.bearingTo(end))

        return asin(sin(r) * sin(b - e)) * radius

    def destination(self, distance, bearing, radius=R_M):
        '''Locates the destination from this point after having
           travelled the given distance on the given initial bearing.

           @param distance: Distance travelled (same units as radius).
           @param bearing: Bearing from this point (compass degrees).
           @keyword radius: Mean earth radius (meter).

           @return: Destination point (L{LatLon}).

           @example:

           >>> p1 = LatLon(51.4778, -0.0015)
           >>> p2 = p1.destination(7794, 300.7)
           >>> p2.toStr()  # '51.5135°N, 000.0983°W'

           @JSname: I{destinationPoint}.
        '''
        # see http://williams.best.vwh.net/avform.htm#LL
        a, b = self.to2ab()

        r = float(distance) / float(radius)  # angular distance in radians
        t = radians(bearing)

        return _destination2(a, b, r, t, h=self.height)

    def distanceTo(self, other, radius=R_M):
        '''Computes the distance from this to an other point.

           @param other: The other point (L{LatLon}).
           @keyword radius: Mean earth radius (meter).

           @return: Distance between this and the other point
                    (in the same units as radius).

           @raise TypeError: The other point is not L{LatLon}.

           @example:

           >>> p1 = LatLon(52.205, 0.119)
           >>> p2 = LatLon(48.857, 2.351);
           >>> d = p1.distanceTo(p2)  # 404300
        '''
        self.others(other)

        a1, b1 = self.to2ab()
        a2, b2 = other.to2ab()

        r, _, _ = _haversine3(a2, a1, b2 - b1)
        return r * float(radius)

    def greatCircle(self, bearing):
        '''Computes vector normal to great circle obtained by heading
           on the given initial bearing from this point.

           Direction of vector is such that initial bearing vector
           b = c × n, where n is an n-vector representing this point.

           @param bearing: Bearing from this point (compass degrees).

           @return: Vector representing great circle (L{Vector3d}).

           @example:

           >>> p = LatLon(53.3206, -1.7297)
           >>> g = p.greatCircle(96.0)
           >>> g.toStr()  # (-0.794, 0.129, 0.594)
        '''
        a, b = self.to2ab()
        t = radians(bearing)

        ca, cb, ct = map1(cos, a, b, t)
        sa, sb, st = map1(sin, a, b, t)

        return Vector3d(sb * ct - cb * sa * st,
                       -cb * ct - sb * sa * st,
                        ca * st)  # XXX .unit()?

    def intermediateTo(self, other, fraction):
        '''Locates the point at given fraction between this and an
           other point.

           @param other: The other point (L{LatLon}).
           @param fraction: Fraction between both points (float, 0.0 =
                            this point, 1.0 = the other point).

           @return: Intermediate point (L{LatLon}).

           @raise TypeError: The other point is not L{LatLon}.

           @example:

           >>> p1 = LatLon(52.205, 0.119)
           >>> p2 = LatLon(48.857, 2.351)
           >>> p = p1.intermediateTo(p2, 0.25)  # 51.3721°N, 000.7073°E
        '''
        self.others(other)

        if fraction < EPS:
            a, b, h = self.to3llh()
        elif fraction > EPS1:
            a, b, h = other.to3llh()
        else:
            a1, b1 = self.to2ab()
            a2, b2 = other.to2ab()

            r, ca2, ca1 = _haversine3(a2, a1, b2 - b1)
            if r > EPS:
                cb1, cb2               = map1(cos, b1, b2)
                sb1, sb2, sa1, sa2, sr = map1(sin, b1, b2, a1, a2, r)

                a = sin((1 - fraction) * r) / sr
                b = sin(     fraction  * r) / sr

                x = a * ca1 * cb1 + b * ca2 * cb2
                y = a * ca1 * sb1 + b * ca2 * sb2
                z = a * sa1       + b * sa2

                a = atan2(z, hypot(x, y))
                b = atan2(y, x)
            else:  # points too close
                a = favg(a1, a2, f=fraction)
                b = favg(b1, b2, f=fraction)

            h = self._alter(other, f=fraction)
            a, b = degrees90(a), degrees180(b)

        return LatLon(a, b, height=h)  # XXX self.topsub(a, b, ...)

    def intersection(self, bearing, start2, bearing2):
        '''Locates the intersection of two paths each defined by
           a start point and an initial bearing.

           @param bearing: Initial bearing from this point (compass degrees).
           @param start2: Start point of second path (L{LatLon}).
           @param bearing2: Initial bearing from start2 (compass degrees).

           @return: Intersection point (L{LatLon}).

           @raise TypeError: Point start2 is not a L{LatLon}.

           @raise ValueError: Intersection is ambiguous or infinite
                              or the paths are parallel or coincide.

           @example:

           >>> p = LatLon(51.8853, 0.2545)
           >>> s = LatLon(49.0034, 2.5735)
           >>> i = p.intersection(108.547, s, 32.435)  # '50.9078°N, 004.5084°E'
        '''
        return intersection(self, bearing, start2, bearing2)

    def isEnclosedBy(self, points):
        '''Tests whether this point is enclosed by the polygon
           defined by a list, sequence, set or tuple of points.

           @param points: The points defining the polygon (L{LatLon}[]).

           @return: True if the polygon encloses this point (bool).

           @raise ValueError: Too few points or non-convex polygon.

           @raise TypeError: Some points are not L{LatLon}.

           @example:

           >>> b = LatLon(45,1), LatLon(45,2), LatLon(46,2), LatLon(46,1)
           >>> p = LatLon(45,1, 1.1)
           >>> inside = p.isEnclosedBy(b)  # True
        '''
        n, points = self.points(points)

        # get great-circle vector for each edge
        gc, v1 = [], points[n-1].toVector3d()
        for p in points:
            v2 = p.toVector3d()
            gc.append(v1.cross(v2))
            v1 = v2

        v = self.toVector3d()
        # check whether this point on same side of all
        # polygon edges (to the left or right depending
        # on anti-/clockwise polygon direction)
        t0 = gc[0].angleTo(v) > PI_2  # True if on the right
        for i in range(1, n):
            ti = gc[i].angleTo(v) > PI_2
            if ti != t0:  # different sides of edge i
                return False  # outside

        # check for convex polygon (otherwise
        # the test above is not reliable)
        gc1 = gc[n-1]
        for gc2 in gc:
            # angle between gc vectors, signed by direction of v
            if gc1.angleTo(gc2, vSign=v) < 0:
                raise ValueError('non-convex: %r' % (points[:3],))
            gc1 = gc2

        return True  # inside

#   def isWithin(self, point1, point2):
#       '''Tests whether this point is within the extent of a
#          segment joining two other points.
#
#          @raise NotImplementedError: Not available.
#
#          @raise TypeError: One of the points is not L{LatLon}.
#
#          @JSname: I{isWithinExtent}.
#       '''
#       self.others(point1, name='point1')
#       self.others(point2, name='point2')
#       raise self.notImplemented('isWithin')

    def midpointTo(self, other):
        '''Finds the midpoint between this and an other point.

           @param other: The other point (L{LatLon}).

           @return: Midpoint (L{LatLon}).

           @raise TypeError: The other point is not L{LatLon}.

           @example:

           >>> p1 = LatLon(52.205, 0.119)
           >>> p2 = LatLon(48.857, 2.351)
           >>> m = p1.midpointTo(p2)  # '50.5363°N, 001.2746°E'
        '''
        self.others(other)

        # see http://mathforum.org/library/drmath/view/51822.html
        a1, b1 = self.to2ab()
        a2, b2 = other.to2ab()

        db = b2 - b1

        ca1, ca2, cdb = map1(cos, a1, a2, db)
        sa1, sa2, sdb = map1(sin, a1, a2, db)

        x = ca2 * cdb + ca1
        y = ca2 * sdb

        a = atan2(sa1 + sa2, hypot(x, y))
        b = atan2(y, x) + b1

        return LatLon(degrees90(a), degrees180(b), height=self._alter(other))

#   def nearestOn(self, point1, point2):
#       '''Locates the point closest to the segment between two points
#          and this point.
#
#          @raise NotImplementedError: Not available.
#
#          @raise TypeError: One of the points is not L{LatLon}.
#
#          @JSname: I{nearestPointOnSegment}.
#       '''
#       self.others(point1, name='point1')
#       self.others(point2, name='point2')
#       raise self.notImplemented('nearestOn')

    def toVector3d(self):
        '''Converts this point to a vector normal to earth's surface.

           @return: Vector representing this point (L{Vector3d}).
        '''
        if self._v3d is None:
            x, y, z = self.to3xyz()
            self._v3d = Vector3d(x, y, z)  # .unit()
        return self._v3d


_Trll = LatLon(0, 0)  #: (INTERNAL) Reference instance (L{LatLon}).


def intersection(start1, bearing1, start2, bearing2):
    '''Return the intersection point of two paths each defined
       by a start point and an initial bearing.

       @param start1: Start point of first path (L{LatLon}).
       @param bearing1: Initial bearing from start1 (compass degrees).
       @param start2: Start point of second path (L{LatLon}).
       @param bearing2: Initial bearing from start2 (compass degrees).

       @return: Intersection point (L{LatLon}).

       @raise TypeError: Point start1 or start2 is not L{LatLon}.

       @raise ValueError: Intersection is ambiguous or infinite
                          or the paths are parallel or coincide.

       @example:

       >>> p = LatLon(51.8853, 0.2545)
       >>> s = LatLon(49.0034, 2.5735)
       >>> i = intersection(p, 108.547, s, 32.435)  # '50.9078°N, 004.5084°E'
    '''
    _Trll.others(start1, name='start1')
    _Trll.others(start2, name='start2')

    # see http://williams.best.vwh.net/avform.htm#Intersection
    a1, b1 = start1.to2ab()
    a2, b2 = start2.to2ab()

    r12, ca2, ca1 = _haversine3(a2, a1, b2 - b1)
    if abs(r12) < EPS:
        raise ValueError('intersection %s: %r vs %r' % ('parallel', start1, start2))

    sa1, sa2, sr12 = map1(sin, a1, a2, r12)
    x1, x2 = (sr12 * ca1), (sr12 * ca2)
    if min(map1(abs, x1, x2)) < EPS:
        raise ValueError('intersection %s: %r vs %r' % ('parallel', start1, start2))

    cr12 = cos(r12)
    t1, t2 = map1(acos, (sa2 - sa1 * cr12) / x1,
                        (sa1 - sa2 * cr12) / x2)
    if sin(b2 - b1) > 0:
        t12, t21 = t1, PI2 - t2
    else:
        t12, t21 = PI2 - t1, t2

    t13, t23 = map1(radians, bearing1, bearing2)
    x1, x2 = map1(wrapPI, t13 - t12,  # angle 2-1-3
                          t21 - t23)  # angle 1-2-3
    sx1, sx2 = map1(sin, x1, x2)
    if sx1 == 0 and sx2 == 0:
        raise ValueError('intersection %s: %r vs %r' % ('infinite', start1, start2))
    sx3 = sx1 * sx2
    if sx3 < 0:
        raise ValueError('intersection %s: %r vs %r' % ('ambiguous', start1, start2))
    cx1, cx2 = map1(cos, x1, x2)

    x3 = acos(cr12 * sx3 - cx2 * cx1)
    r13 = atan2(sr12 * sx3, cx2 + cx1 * cos(x3))

    return _destination2(a1, b1, r13, t13, h=start1._alter(start2))


def meanOf(points, height=None):
    '''Computes the geographic mean of the supplied points.

       @param points: Points to be averaged (L{LatLon}[]).
       @keyword height: Height to use inlieu of mean (meter).

       @return: Point at geographic mean and height (L{LatLon}).

       @raise TypeError: Some points are not L{LatLon}.

       @raise ValueError: If no points.
    '''
    # geographic mean
    n, points = _Trll.points(points, closed=False)
    m = sumOf(p.Vector3d() for p in points)
    a, b = m.to2ll()
    if height is None:
        h = fsum(p.height for p in points) / n
    else:
        h = height
    return LatLon(a, b, height=h)


def _destination2(a, b, r, t, h=0):
    '''(INTERNAL) Compute destination.

       @param a: Latitude (radians).
       @param b: Longitude (radians).
       @param r: Angular distance (radians).
       @param t: Bearing (radians).
       @param h: Height (meter).

       @return: Destination (L{LatLon}).
    '''
    ca, cr, ct = map1(cos, a, r, t)
    sa, sr, st = map1(sin, a, r, t)

    a  = asin(ct * sr * ca + cr * sa)
    b += atan2(st * sr * ca, cr - sa * sin(a))
    return LatLon(degrees90(a), degrees180(b), height=h)


def _haversine3(a2, a1, b21):
    '''(INTERNAL) Compute the angular distance.

       @param a2: Latitude2 (radians).
       @param a1: Latitude1 (radians).
       @param b21: Longitude delta (radians).

       @return: 3-Tuple (angle, cos(a2), cos(a1))

       @see: U{http://www.movable-type.co.uk/scripts/latlong.html}

       @see: U{http://williams.best.vwh.net/avform.htm#Dist}
    '''
    ca2, ca1 = map1(cos, a2, a1)
    h = hsin(a2 - a1) + ca1 * ca2 * hsin(b21)  # haversine
    try:
        r = atan2(sqrt(h), sqrt(1 - h)) * 2  # == asin(sqrt(h)) * 2
    except ValueError:
        r = 0 if h < 0.5 else PI
    return r, ca2, ca1

# **) MIT License
#
# Copyright (C) 2016-2017 -- mrJean1 at Gmail dot com
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

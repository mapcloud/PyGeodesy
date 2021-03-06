
# -*- coding: utf-8 -*-

# Test degrees, minutes, seconds functions.

__all__ = ('Tests',)
__version__ = '17.04.07'

from tests import Tests as _Tests

from pygeodesy import F_D, F_DM, F_DMS, \
                      compassPoint, parse3llh, parseDMS, toDMS


class Tests(_Tests):

    def testDms(self):
        # dms module tests
        self.test('parseDMS', parseDMS(  '0.0°'), '0.0')
        self.test('parseDMS', parseDMS(    '0°'), '0.0')
        self.test('parseDMS', parseDMS('''000°00'00"'''),   '0.0')
        self.test('parseDMS', parseDMS('''000°00'00.0"'''), '0.0')
        self.test('parseDMS', parseDMS('''000° 00'00"'''),    '0.0')
        self.test('parseDMS', parseDMS('''000°00 ' 00.0"'''), '0.0')

        x = parse3llh('000° 00′ 05.31″W, 51° 28′ 40.12″ N')
        x = ', '.join('%.6f' % a for a in x)  # XXX fStr
        self.test('parse3llh', x, '51.477811, -0.001475, 0.000000')

        for a, x in (((),            '''45°45'45.36"'''),
                     ((F_D, None),     '45.7626°'),
                     ((F_DM, None),    "45°45.756'"),
                     ((F_DMS, None), '''45°45'45.36"'''),
                     ((F_D, 6),     '45.7626°'),
                     ((F_DM, -4),   "45°45.7560'"),
                     ((F_DMS, 2), '''45°45'45.36"''')):
            self.test('toDMS', toDMS(45.76260, *a), x)

        for a, x in (((1,),   'N'),
                     ((0,),   'N'),
                     ((-1,),  'N'),
                     ((359,), 'N'),
                     ((24,),   'NNE'),
                     ((24, 1), 'N'),
                     ((24, 2), 'NE'),
                     ((24, 3), 'NNE'),
                     ((226,),   'SW'),
                     ((226, 1), 'W'),
                     ((226, 2), 'SW'),
                     ((226, 3), 'SW'),
                     ((237,),   'WSW'),
                     ((237, 1), 'W'),
                     ((237, 2), 'SW'),
                     ((237, 3), 'WSW')):
            self.test('compassPoint', compassPoint(*a), x)


if __name__ == '__main__':

    from pygeodesy import dms  # private

    t = Tests(__file__, __version__, dms)
    t.testDms()
    t.results()
    t.exit()

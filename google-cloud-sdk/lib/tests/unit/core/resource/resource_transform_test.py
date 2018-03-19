# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the resource_transform module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import times
from tests.lib import test_case


_FLOAT_RESOURCE = [
    9e-08,
    -9e-07,
    9e-06,
    -9e-05,
    0.0009,
    -0.009,
    0.09,
    -0.9,
    1.00000009,
    -1.0000009,
    1.000009,
    -1.00009,
    1.0009,
    -1.009,
    1.009,
    -1.09,
    1.9,
    -1.3333333,
    1.6666666,
    -12.345678901,
    123.45678901,
    -1234.5678901,
    12345.678901,
    -123456.78901,
    1234567.8901,
    -12345678.901,
    123456789.01,
    -123456789.012,
    1e+00,
    1e+01,
    1e+02,
    1e+03,
    1e+04,
    1e+05,
    1e+06,
    1e+07,
    1e+08,
    1e+09,
    1e-01,
    1e-02,
    1e-03,
    1e-04,
    1e-05,
    1e-06,
    1e-07,
    1e-08,
    1e-09,
]


class ResourceTransformTest(test_case.Base):

  class Time(object):

    def __init__(self, secs):
      self._secs = secs

    def IsoFormat(self):
      return '{0}T'.format(self._secs)

  class Resolution1(object):

    def __init__(self, w, h):
      self.width = w
      self.height = h

  class Resolution2(object):

    def __init__(self, w, h):
      self.col = w
      self.row = h

  class Resolution3(object):

    def __init__(self, w, h):
      self.col = w
      self.line = h

  class Resolution4(object):

    def __init__(self, w, h):
      self.screenx = w
      self.screeny = h

  class Resolution5(object):

    def __init__(self, w, h):
      self.x = w
      self.y = h

  class Resolution6(object):

    def __init__(self, w, h):
      self.foo = w
      self.bar = h

  class SelfLink1(object):

    def __init__(self):
      self.selfLink = 'https://oo/selfLink1'  # pylint: disable=invalid-name

  class SelfLink2(object):

    def __init__(self):
      self.SelfLink = 'https://oo/SelfLink2'  # pylint: disable=invalid-name

  def Colorize(self, string, color, **kwargs):
    return '<{color}>{string}</{color}>'.format(color=color, string=string)

  def SetUp(self):

    class Group(object):

      def __init__(self, code=None, message=None):
        self.code = code
        self.message = message

    self._resource = [
        {
            'path': '/dir/base.suffix',
            'time': self.Time(12345678),
            'group': [
                Group(123, 'Message for 123.'),
                Group(456, 'Message for 456.'),
                Group(789, 'Message for 789.'),
                ],
            # The TransformList tests use the list and dict entries. There is
            # nothing special about the values or number of items except that
            # TransformList formats them correctly.
            'list': [1, 2, 3, 4],
            'dict': {'a': 1, 'b': 2, 'c': 3, 'd': 4},
            'res': self.Resolution1(100, 200),
            'size': 1024 * (1024 * 1024 * 1024 + 123),
            'selfLink': 'https://oo/before/regions/region-a/foo/bar',
            'status': 'PASSED',
            'value': None,
            },
        {
            'path': '/dir/base',
            'time': self.Time(23456789),
            'group': [
                Group(123, 'Message for 123.'),
                ],
            'list': ['a', 'b', 'c', 'd'],
            'dict': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'},
            'res': self.Resolution2(100, 200),
            'size': 1024 * (1024 * 1024 + 123),
            'selfLink': 'https://oo/before/zones/zone-b/foo/bar',
            'status': 'FAILED',
            'value': 0,
            },
        {
            'path': 'dir/base.suffix',
            'time': self.Time(34567890),
            'group': [
                Group(456, 'Message for 456.'),
                ],
            'list': [1, 'b', 3, 'd'],
            'dict': {'B': 'b', 'D': 'd'},
            'res': self.Resolution3(100, 200),
            'size': 1024 * (1024 + 123),
            'selfLink': 'https://oo/before/projects/project-c/foo%2Fbar',
            'status': 'WARNING',
            'value': True,
            },
        {
            'path': '\\dir\\base',
            'time': self.Time(45678901),
            'group': [
                Group(789, 'Message for 789.'),
                ],
            'list': [1, 2, 3, 4],
            'dict': None,
            'res': self.Resolution4(100, 200),
            'size': 1024 + 123,
            'selfLink': 'https://oo/before/zones/all/zones/zone-b/foo/bar',
            'status': 'DOWN',
            'value': [],
            },
        {
            'path': 'base.suffix',
            'time': self.Time(56789012),
            'list': [1, 2, 3, 4],
            'dict': 'line of text',
            'res': self.Resolution5(100, 200),
            'size': 123,
            'selfLink': 'https://oo/before/zone/all/zones/zone-b/foo%2Fbar',
            'status': 'UNKNOWN',
            'value': [1],
            },
        {
            'path': '',
            'time': self.Time(67890123),
            'group': [],
            'list': [1, 2, 3, 4],
            'dict': 1234,
            'res': self.Resolution6(100, 200),
            'size': 0,
            'selfLink': 'https://oo/before/zones/',
            'status': '',
            'value': '',
            },
        {
            'path': '',
            'time': self.Time(67890123),
            'group': [],
            'list': [1, 2, 3, 4],
            'res': self.Resolution6(100, 200),
            'size': 1024 * (1024 * 1024 * 1024 * 1024 + 123),
            'selfLink': 'https://oo/before/zones',
            'status': None,
            'value': '',
            },
    ]
    self.StartObjectPatch(console_attr, 'Colorizer').side_effect = self.Colorize

  def TearDown(self):
    self._resource = None

  def Run(self, resource, key, transform, args, expected,
          kwargs=None, projection=None):
    """Applies transform to the value of key in each resource item.

    Args:
      resource: The resource to transform.
      key: Resource key name.
      transform: The transform function to apply to the key value.
      args: The list of arg strings for the transform function.
      expected: The list of expected transformed values, one per resource item.
      kwargs: Optional name=value args.
      projection: The parent ProjectionSpec.
    """
    self.maxDiff = 4096
    actual = []
    if kwargs is None:
      kwargs = {}
    doc = transform.__doc__
    if doc and resource_projection_spec.PROJECTION_ARG_DOC in doc:
      # The second transform arg is the parent ProjectionSpec.
      args = [projection or resource_projector.Compile('').Projection()] + args
    for item in resource:
      value = item.get(key, None) if key else item
      actual.append(transform(value, *args, **kwargs))
    self.assertEqual(expected, actual)

  def testTransformBaseName(self):
    self.Run(self._resource, 'path', resource_transform.TransformBaseName, [],
             ['base.suffix', 'base', 'base.suffix', 'base', 'base.suffix', '',
              ''])

  def testTransformColorNoPatterns(self):
    self.Run(self._resource, 'status', resource_transform.TransformColor, [],
             ['PASSED', 'FAILED', 'WARNING', 'DOWN', 'UNKNOWN', '', 'None'])

  def testTransformColor(self):
    self.Run(self._resource, 'status', resource_transform.TransformColor,
             ['FAIL', 'WARN', 'PASS', 'DOWN'],
             ['<green>PASSED</green>',
              '<red>FAILED</red>',
              '<yellow>WARNING</yellow>',
              '<blue>DOWN</blue>',
              'UNKNOWN',
              '',
              'None'])

  def testTransformDateUTC(self):
    resource = [1234567890, 1244567890]
    kwargs = {
        'tz_default': 'UTC'
    }
    expected = ['2009-02-13T23:31:30', '2009-06-09T17:18:10']
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUTCAllParts(self):
    resource = [
        {
            'year': '2009', 'month': '02', 'day': '13',
            'hour': '18', 'minute': '31', 'second': '30',
            'millisecond': '123', 'microsecond': '456', 'nanosecond': '789'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'millisecond': '123', 'microsecond': '456', 'nanosecond': '789'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'nanosecond': '999999999'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'nanosecond': 999999999
        },
    ]
    kwargs = {
        'format': '%Y-%m-%dT%H:%M:%S.%f%z',
        'tz_default': 'UTC'
    }
    expected = [
        '2009-02-13T18:31:30.123456+0000',
        '2009-06-09T13:18:10.123456+0000',
        '2009-06-09T13:18:10.999999+0000',
        '2009-06-09T13:18:10.999999+0000',
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUTCThreeParts(self):
    resource = [
        {
            'month': '02', 'day': '13', 'hour': '18',
        },
        {
            'month': 6, 'day': 9, 'hour': 13,
        },
    ]
    kwargs = {
        'format': '%m-%dT%H%z',
        'tz_default': 'UTC'
    }
    expected = [
        '02-13T18+0000',
        '06-09T13+0000'
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUTCTwoParts(self):
    resource = [
        {
            'month': '02', 'day': '13',
        },
        {
            'month': 6, 'day': 9,
        },
    ]
    kwargs = {
        'format': '%m-%d%z',
        'tz': 'UTC'
    }
    expected = [
        '',
        ''
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateFromStringTzDefault(self):
    resource = ['2016-01-19T10:51:11.941-08:00',
                '2016-01-19T10:51:11.941-0800',
                '2016-01-19T10:51:11.941',
                'February 11, 2015 12:00:00 EST']
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                times.FormatDateTime(
                    times.ParseDateTime('2016-01-19T10:51:11.941'),
                    '%Y-%m-%dT%H:%M:%S.%f%z'),
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected)

  def testTransformDateFromStringTzDefaultLocal(self):
    resource = ['2016-01-19T10:51:11.941-08:00',
                '2016-01-19T10:51:11.941-0800',
                '2016-01-19T10:51:11.941',
                'February 11, 2015 12:00:00 EST']
    kwargs = {
        'tz_default': 'local'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                times.FormatDateTime(
                    times.ParseDateTime('2016-01-19T10:51:11.941'),
                    '%Y-%m-%dT%H:%M:%S.%f%z'),
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateFromStringTzDefaultUTC(self):
    resource = ['2016-01-19T10:51:11.941-08:00',
                '2016-01-19T10:51:11.941-0800',
                '2016-01-19T10:51:11.941',
                'February 11, 2015 12:00:00 EST']
    kwargs = {
        'tz_default': 'UTC'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000+0000',
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateFromDateTimeTzDefaultUTC(self):
    strings = ['2016-01-19T10:51:11.941-08:00',
               '2016-01-19T10:51:11.941-0800',
               '2016-01-19T10:51:11.941',
               'February 11, 2015 12:00:00 EST']
    resource = [times.ParseDateTime(x, tzinfo=times.UTC) for x in strings]
    kwargs = {
        'tz_default': 'UTC'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000+0000',
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateFromDateTimeTzDefaultUTCTzUsPacific(self):
    strings = ['2016-01-19T10:51:11.941-08:00',
               '2016-01-19T10:51:11.941-0800',
               '2016-01-19T10:51:11.941',
               'February 11, 2015 12:00:00 EST']
    resource = [times.ParseDateTime(x, tzinfo=times.UTC) for x in strings]
    kwargs = {
        'tz_default': 'UTC',
        'tz': 'US/Pacific'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T02:51:11.941000-0800',
                '2015-02-11T09:00:00.000000-0800']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateFromSerializedDateTimeTzDefaultUTC(self):
    strings = ['2016-01-19T10:51:11.941-08:00',
               '2016-01-19T10:51:11.941-0800',
               '2016-01-19T10:51:11.941',
               'February 11, 2015 12:00:00 EST']
    serialize = resource_projector.Compile().Evaluate
    resource = [serialize(times.ParseDateTime(x, tzinfo=times.UTC))
                for x in strings]
    kwargs = {
        'tz_default': 'UTC'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000+0000',
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateFromSerializedDateTimeTzDefaultUTCTzUsPacific(self):
    strings = ['2016-01-19T10:51:11.941-08:00',
               '2016-01-19T10:51:11.941-0800',
               '2016-01-19T10:51:11.941',
               'February 11, 2015 12:00:00 EST']
    serialize = resource_projector.Compile().Evaluate
    resource = [serialize(times.ParseDateTime(x, tzinfo=times.UTC))
                for x in strings]
    kwargs = {
        'tz_default': 'UTC',
        'tz': 'US/Pacific'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T02:51:11.941000-0800',
                '2015-02-11T09:00:00.000000-0800']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateUSEastern(self):
    resource = [1234567890123, 1244567890123]
    kwargs = {
        'format': '%Y-%m-%dT%H:%M:%S%z',
        'unit': '1000',
        'tz_default': 'US/Eastern'
    }
    expected = ['2009-02-13T18:31:30-0500', '2009-06-09T13:18:10-0400']
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUSPacific(self):
    resource = [1234567890123456, 1244567890123456]
    kwargs = {
        'format': '%Y-%m-%dT%H:%M:%S%z',
        'unit': '1000000',
        'tz_default': 'US/Pacific'
    }
    expected = ['2009-02-13T15:31:30-0800', '2009-06-09T10:18:10-0700']
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUSEasternAllParts(self):
    resource = [
        {
            'year': '2009', 'month': '02', 'day': '13',
            'hour': '18', 'minute': '31', 'second': '30',
            'millisecond': '123', 'microsecond': '456', 'nanosecond': '789'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'millisecond': '123', 'microsecond': '456', 'nanosecond': '789'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'nanosecond': '999999999'
        },
        {
            'year': '2009', 'month': '06', 'day': '09',
            'hour': '13', 'minute': '18', 'second': '10',
            'nanosecond': 999999999
        },
    ]
    kwargs = {
        'format': '%Y-%m-%dT%H:%M:%S.%f%z',
        'tz_default': 'US/Eastern'
    }
    expected = [
        '2009-02-13T18:31:30.123456-0500',
        '2009-06-09T13:18:10.123456-0400',
        '2009-06-09T13:18:10.999999-0400',
        '2009-06-09T13:18:10.999999-0400',
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUSEasternThreeParts(self):
    resource = [
        {
            'month': '02', 'day': '13', 'hour': '18',
        },
        {
            'month': 6, 'day': 9, 'hour': 13,
        },
    ]
    kwargs = {
        'format': '%m-%dT%H%z',
        'tz_default': 'US/Eastern'
    }
    expected = [
        '02-13T18-0500',
        '06-09T13-0400'
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateUSEasternTwoParts(self):
    resource = [
        {
            'month': '02', 'day': '13',
        },
        {
            'month': 6, 'day': 9,
        },
    ]
    kwargs = {
        'format': '%m-%d%z',
        'tz': 'US/Eastern'
    }
    expected = [
        '',
        ''
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateFromStringUSEastern(self):
    resource = ['2016-01-19T10:51:11.941-08:00',
                '2016-01-19T10:51:11.941-0800',
                '2016-01-19T10:51:11.941',
                'February 11, 2015 12:00:00']
    kwargs = {
        'tz_default': 'US/Eastern'
    }
    expected = ['2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0800',
                '2016-01-19T10:51:11.941000-0500',
                '2015-02-11T12:00:00.000000-0500']
    self.Run(resource, None, resource_transform.TransformDate,
             ['%Y-%m-%dT%H:%M:%S.%f%z'], expected, kwargs)

  def testTransformDateLocal(self):
    resource = [1234567890, 1244567890]
    kwargs = {}
    expected = [
        times.FormatDateTime(times.GetDateTimeFromTimeStamp(resource[0]),
                             '%Y-%m-%dT%H:%M:%S'),
        times.FormatDateTime(times.GetDateTimeFromTimeStamp(resource[1]),
                             '%Y-%m-%dT%H:%M:%S'),
    ]
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDateErrors(self):
    resource = [1e12]
    kwargs = {'undefined': 'UNDEFINED'}
    expected = ['UNDEFINED']
    self.Run(resource, None, resource_transform.TransformDate, [], expected,
             kwargs)

  def testTransformDecodeBase64(self):
    resource = ['VGhpcyBpcyBiYXNlNjQgZW5jb2RlZC4=',
                'This is not base64 encoded.',
                12345]
    kwargs = {
        'undefined': b'ERROR'
    }
    expected = [b'This is base64 encoded.',
                b'ERROR',
                b'ERROR']
    self.Run(resource, None, resource_transform.TransformDecode,
             ['base64'], expected, kwargs)

  def testTransformDecodeBase64UrlSafe(self):
    # URL Safe encoded base64 strings have '-' and '_' in place of '+' and '/'
    resource = ['ab==', 'ab/+', 'ab_-']
    kwargs = {
        'undefined': b'ERROR'
    }
    expected = [b'i', b'i\xbf\xfe', b'i\xbf\xfe']
    self.Run(resource, None, resource_transform.TransformDecode,
             ['base64'], expected, kwargs)

  def testTransformDecodeUtf8(self):
    resource = [b'This is ASCII text.',
                b'This is b\xaad UTF-8 text.',
                12345]
    kwargs = {
        'undefined': b'ERROR'
    }
    expected = ['This is ASCII text.',
                'This is b\ufffdd UTF-8 text.',
                b'ERROR']
    self.Run(resource, None, resource_transform.TransformDecode,
             ['utf8'], expected, kwargs)

  def testTransformDecodeUnknownEncoding(self):
    resource = ['This is ASCII text.']
    kwargs = {
        'undefined': b'ERROR'
    }
    expected = [b'ERROR']
    self.Run(resource, None, resource_transform.TransformDecode,
             ['UnKnOwN'], expected, kwargs)

  def testTransformDurationDefault(self):
    resource = [66, 10 * 60, 24 * 60 * 60, 28 * 24 * 60 * 60, 'P0', 'PT28M']
    expected = ['PT1M6S', 'PT10M', 'P1D', 'P28D', 'P0', 'PT28M']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected)

  def testTransformDurationCalendar(self):
    resource = [66, 10 * 60, 24 * 60 * 60, 28 * 24 * 60 * 60, 'P0', 'PT28M']
    expected = ['PT1M6S', 'PT10M', 'P1D', 'P28D', 'P0', 'PT28M']
    kwargs = {
        'calendar': 'true',
    }
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs=kwargs)

  def testTransformDurationExact(self):
    resource = [66, 10 * 60, 24 * 60 * 60, 28 * 24 * 60 * 60, 'P0', 'PT28M']
    expected = ['PT1M6S', 'PT10M', 'PT24H', 'PT672H', 'P0', 'PT28M']
    kwargs = {
        'calendar': 'false',
    }
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs=kwargs)

  def testTransformDurationBadFloat(self):
    resource = ['not a float']
    expected = ['']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected)

  def testTransformDurationBadParts(self):
    resource = [66]
    kwargs = {
        'parts': '1.234',
    }
    expected = ['']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationBadPrecision(self):
    resource = [66]
    kwargs = {
        'precision': '1.234',
    }
    expected = ['']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationBadUnit(self):
    resource = [66]
    kwargs = {
        'unit': '1.234',
    }
    expected = ['PT53.485S']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationBadStartOrEnd(self):
    resource = [
        {
            'startTime': 'not a time',
            'endTime': '2016-01-19T10:51:11.000000Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.000000Z',
            'endTime': 'not a time',
        },
    ]
    kwargs = {
        'start': 'startTime',
        'end': 'endTime',
    }
    expected = ['', '']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationStartEnd(self):
    resource = [
        {
            'startTime': '2016-01-19T10:51:11.000000Z',
            'endTime': '2016-01-19T10:51:11.000000Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.000000Z',
            'endTime': '2016-01-19T10:51:11.941000-0800',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000-0800',
            'endTime': '2016-01-19T10:51:11.000000Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:51:13.000149-00:00',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:51:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:53:15.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T14:53:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-20T14:53:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-09-20T14:53:12.000149Z',
        },
        {
            'startTime': '2014-01-19T10:51:11.941000Z',
            'endTime': '2016-09-20T14:53:12.000149Z',
        },
    ]
    kwargs = {
        'start': 'startTime',
        'end': 'endTime',
    }
    expected = ['P0', 'PT8H0.941S', '-PT8H0.941S', 'PT1.059S', 'PT0.059S',
                'PT2M3.059S', 'PT4H2M0.059S', 'P1DT4H2M', 'P245DT4H2M',
                'P2Y244D']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationStartEndPrecision0(self):
    resource = [
        {
            'startTime': '2016-01-19T10:51:11.000000Z',
            'endTime': '2016-01-19T10:51:11.000000Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.000000Z',
            'endTime': '2016-01-19T10:51:11.941000-0800',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000-0800',
            'endTime': '2016-01-19T10:51:11.000000Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:51:13.000149-00:00',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:51:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T10:53:15.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-19T14:53:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-01-20T14:53:12.000149Z',
        },
        {
            'startTime': '2016-01-19T10:51:11.941000Z',
            'endTime': '2016-09-20T14:53:12.000149Z',
        },
        {
            'startTime': '2014-01-19T10:51:11.941000Z',
            'endTime': '2016-09-20T14:53:12.000149Z',
        },
    ]
    kwargs = {
        'start': 'startTime',
        'end': 'endTime',
        'precision': '0',
    }
    expected = ['P0', 'PT8H1S', '-PT8H1S', 'PT1S', 'P0', 'PT2M3S',
                'PT4H2M', 'P1DT4H2M', 'P245DT4H2M', 'P2Y244D']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationStartNow(self):
    self.StartObjectPatch(
        times,
        'Now',
        return_value=times.ParseDateTime('2016-01-19T10:51:12.0Z'))
    resource = [
        {'startTime': '2014-01-19T10:51:11.941000Z'},
        {'startTime': '2016-01-19T10:51:11.000000Z'},
        {'startTime': '2016-01-19T10:51:11.941000-0800'},
        {'startTime': '2016-01-19T10:51:11.941000Z'},
        {'startTime': '2016-01-19T10:51:12.000149Z'},
        {'startTime': '2016-01-19T10:51:13.000149-00:00'},
        {'startTime': '2016-01-19T10:53:15.000149Z'},
        {'startTime': '2016-01-19T14:53:12.000149Z'},
        {'startTime': '2016-01-20T14:53:12.000149Z'},
        {'startTime': '2016-09-20T14:53:12.000149Z'},
    ]
    kwargs = {
        'start': 'startTime',
    }
    expected = ['P1Y364D', 'PT1S', '-PT7H59M59.941S', 'PT0.059S', '-P0',
                '-PT1S', '-PT2M3S', '-PT4H2M', '-P1DT4H2M', '-P245DT4H2M']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformDurationDateTimeNow(self):
    self.StartObjectPatch(
        times,
        'Now',
        return_value=times.ParseDateTime('2016-01-19T10:51:12.0Z'))
    resource = [
        '2014-01-19T10:51:11.941000Z',
        '2016-01-19T10:51:11.000000Z',
        '2016-01-19T10:51:11.941000-0800',
        '2016-01-19T10:51:11.941000Z',
        '2016-01-19T10:51:12.000149Z',
        '2016-01-19T10:51:13.000149-00:00',
        '2016-01-19T10:53:15.000149Z',
        '2016-01-19T14:53:12.000149Z',
        '2016-01-20T14:53:12.000149Z',
        '2016-09-20T14:53:12.000149Z',
    ]
    expected = ['P1Y364D', 'PT1S', '-PT7H59M59.941S', 'PT0.059S', '-P0',
                '-PT1S', '-PT2M3S', '-PT4H2M', '-P1DT4H2M', '-P245DT4H2M']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected)

  def testTransformDurationErrors(self):
    resource = [1e12]
    kwargs = {'undefined': 'UNDEFINED'}
    expected = ['UNDEFINED']
    self.Run(resource, None, resource_transform.TransformDuration, [], expected,
             kwargs)

  def testTransformEncodeBase64(self):
    resource = ['This is base64 encoded.',
                12345]
    kwargs = {
        'undefined': 'ERROR'
    }
    expected = ['VGhpcyBpcyBiYXNlNjQgZW5jb2RlZC4=',
                'ERROR']
    self.Run(resource, None, resource_transform.TransformEncode,
             ['base64'], expected, kwargs)

  def testTransformEncodeUtf8(self):
    resource = ['This is ASCII text.',
                12345]
    kwargs = {
        'undefined': 'ERROR'
    }
    expected = ['This is ASCII text.',
                'ERROR']
    self.Run(resource, None, resource_transform.TransformEncode,
             ['utf8'], expected, kwargs)

  def testTransformEncodeUnknownEncoding(self):
    resource = ['This is ASCII text.']
    kwargs = {
        'undefined': 'ERROR'
    }
    expected = ['ERROR']
    self.Run(resource, None, resource_transform.TransformEncode,
             ['UnKnOwN'], expected, kwargs)

  def testTransformEnum(self):
    enums = {'A': 1, 'BB': 2, 'CCC': 3, 'x': 4, 'yy': 5, 'zzz': 6}
    enum_name = 'test'
    enum_data_name = resource_transform.GetTypeDataName(enum_name, 'enum')
    inverse_enum_data_name = resource_transform.GetTypeDataName(
        enum_name, 'inverse-enum')
    symbols = {enum_data_name: enums}
    projection = resource_projector.Compile('', symbols=symbols).Projection()
    resource = [
        {
            'forward': 'A',
            'reverse': 1,
        },
        {
            'forward': 'BB',
            'reverse': 2,
        },
        {
            'forward': 'CCC',
            'reverse': 3,
        },
        {
            'forward': 'x',
            'reverse': 4,
        },
        {
            'forward': 'yy',
            'reverse': 5,
        },
        {
            'forward': 'zzz',
            'reverse': 6,
        },
    ]
    inverse_kwargs = {
        'inverse': 'true'
    }
    expected_undefined = ['', '', '', '', '', '']
    expected_forward = [1, 2, 3, 4, 5, 6]
    expected_reverse = ['A', 'BB', 'CCC', 'x', 'yy', 'zzz']

    # Verify initial symbols.

    self.assertTrue(enum_data_name in projection.symbols)
    self.assertFalse(inverse_enum_data_name in projection.symbols)

    # Normal and inverse tests with no enums defined.

    self.Run(resource, 'forward', resource_transform.TransformEnum,
             [enum_name], expected_undefined)
    self.Run(resource, 'reverse', resource_transform.TransformEnum,
             [enum_name], expected_undefined, kwargs=inverse_kwargs)

    # Inverse should not be in the projection.symbols yet.

    self.assertFalse(inverse_enum_data_name in projection.symbols)

    # Normal and inverse tests with enums defined.

    self.Run(resource, 'forward', resource_transform.TransformEnum,
             [enum_name], expected_forward, projection=projection)
    self.Run(resource, 'reverse', resource_transform.TransformEnum,
             [enum_name], expected_reverse, projection=projection,
             kwargs=inverse_kwargs)

    # The last inverse test should have added inverse to the projection symbols.

    self.assertTrue(inverse_enum_data_name in projection.symbols)

  def testTransformErrorWithMessage(self):
    msg = 'Test error message.'
    with self.assertRaisesRegexp(resource_exceptions.Error, msg):
      self.Run(self._resource, 'error', resource_transform.TransformError,
               [msg], [])

  def testTransformErrorNoMessage(self):
    msg = 'Test error message.'
    resource = [{'error': msg}]
    with self.assertRaisesRegexp(resource_exceptions.Error, msg):
      self.Run(resource, 'error', resource_transform.TransformError,
               [], [])

  def testTransformExtract(self):
    resources = [
        {'k1': 'v1.1', 'k2': 'v1.2', 'k3': 'v1.3'},
        {'k1': 'v2.1', 'k3': 'v2.3'},
        {'k1': 1, 'k2': 2, 'k3': 3},
        {'foo': 'bar'},
        1234,
    ]
    expected = [
        ['v1.1', 'v1.3', 'v1.2'],
        ['v2.1', 'v2.3'],
        [1, 3, 2],
        [],
        [],
    ]

    self.Run(resources, None, resource_transform.TransformExtract,
             ['k1', 'k3', 'k2', 'k4'], expected)

  def testTransformFatal(self):
    msg = 'Test fatal message.'
    with self.assertRaisesRegexp(resource_exceptions.InternalError, msg):
      self.Run(self._resource, 'fatal', resource_transform.TransformFatal,
               [msg], [])

  def testTransformFirstOfNoNames(self):
    self.Run(self._resource, None, resource_transform.TransformFirstOf,
             [],
             ['', '', '', '', '', '', ''])

  def testTransformFirstOfNoNameMatch(self):
    self.Run(self._resource, None, resource_transform.TransformFirstOf,
             ['Foo', 'Bar'],
             ['', '', '', '', '', '', ''])

  def testTransformFirstOfNoClass(self):
    self.Run(self._resource, 'time', resource_transform.TransformFirstOf,
             ['Foo', 'Bar'],
             ['', '', '', '', '', '', ''])

  def testTransformFirstOfClass(self):

    class Object(object):

      def __init__(self):
        self.name = 'foo'
        self.value = 'bar'

    resource = [{'object': Object()}]
    self.Run(resource, 'object', resource_transform.TransformFirstOf,
             ['name', 'value'],
             ['foo'])
    self.Run(resource, 'object', resource_transform.TransformFirstOf,
             ['unknown', 'value'],
             ['bar'])

  def testTransformFirstOfLastNameMatch(self):
    self.Run(self._resource, None, resource_transform.TransformFirstOf,
             ['Foo', 'Bar', 'status'],
             ['PASSED', 'FAILED', 'WARNING', 'DOWN', 'UNKNOWN', '', ''])

  def testTransformFloatWithPrecisionDefault(self):
    expected = [
        '9e-08',
        '-9e-07',
        '9e-06',
        '-9e-05',
        '0.0009',
        '-0.009',
        '0.09',
        '-0.9',
        '1.0',
        '-1.0',
        '1.00001',
        '-1.00009',
        '1.0009',
        '-1.009',
        '1.009',
        '-1.09',
        '1.9',
        '-1.33333',
        '1.66667',
        '-12.3457',
        '123.457',
        '-1234.57',
        '12345.7',
        '-123456.8',
        '1234567.9',
        '-12345678.9',
        '123456789.0',
        '-123456789.0',
        '1.0',
        '10.0',
        '100.0',
        '1000.0',
        '10000.0',
        '100000.0',
        '1000000.0',
        '10000000.0',
        '100000000.0',
        '1e+09',
        '0.1',
        '0.01',
        '0.001',
        '0.0001',
        '1e-05',
        '1e-06',
        '1e-07',
        '1e-08',
        '1e-09',
    ]
    self.Run(_FLOAT_RESOURCE, None, resource_transform.TransformFloat, [],
             expected)

  def testTransformFloatWithPrecision5(self):
    expected = [
        '9e-08',
        '-9e-07',
        '9e-06',
        '-9e-05',
        '0.0009',
        '-0.009',
        '0.09',
        '-0.9',
        '1.0',
        '-1.0',
        '1.0',
        '-1.0001',
        '1.0009',
        '-1.009',
        '1.009',
        '-1.09',
        '1.9',
        '-1.3333',
        '1.6667',
        '-12.346',
        '123.46',
        '-1234.6',
        '12345.7',
        '-123456.8',
        '1234567.9',
        '-12345678.9',
        '123456789.0',
        '-123456789.0',
        '1.0',
        '10.0',
        '100.0',
        '1000.0',
        '10000.0',
        '100000.0',
        '1000000.0',
        '10000000.0',
        '100000000.0',
        '1e+09',
        '0.1',
        '0.01',
        '0.001',
        '0.0001',
        '1e-05',
        '1e-06',
        '1e-07',
        '1e-08',
        '1e-09',
    ]
    self.Run(_FLOAT_RESOURCE, None, resource_transform.TransformFloat, [],
             expected, kwargs={'precision': 5})

  def testTransformFloatWithPrecision8(self):
    expected = [
        '9e-08',
        '-9e-07',
        '9e-06',
        '-9e-05',
        '0.0009',
        '-0.009',
        '0.09',
        '-0.9',
        '1.0000001',
        '-1.0000009',
        '1.000009',
        '-1.00009',
        '1.0009',
        '-1.009',
        '1.009',
        '-1.09',
        '1.9',
        '-1.3333333',
        '1.6666666',
        '-12.345679',
        '123.45679',
        '-1234.5679',
        '12345.679',
        '-123456.79',
        '1234567.9',
        '-12345678.9',
        '123456789.0',
        '-123456789.0',
        '1.0',
        '10.0',
        '100.0',
        '1000.0',
        '10000.0',
        '100000.0',
        '1000000.0',
        '10000000.0',
        '100000000.0',
        '1e+09',
        '0.1',
        '0.01',
        '0.001',
        '0.0001',
        '1e-05',
        '1e-06',
        '1e-07',
        '1e-08',
        '1e-09',
    ]
    self.Run(_FLOAT_RESOURCE, None, resource_transform.TransformFloat, [],
             expected, kwargs={'precision': 8})

  def testTransformFloatWithSpecE(self):
    expected = [
        '9.000000e-08',
        '-9.000000e-07',
        '9.000000e-06',
        '-9.000000e-05',
        '9.000000e-04',
        '-9.000000e-03',
        '9.000000e-02',
        '-9.000000e-01',
        '1.000000e+00',
        '-1.000001e+00',
        '1.000009e+00',
        '-1.000090e+00',
        '1.000900e+00',
        '-1.009000e+00',
        '1.009000e+00',
        '-1.090000e+00',
        '1.900000e+00',
        '-1.333333e+00',
        '1.666667e+00',
        '-1.234568e+01',
        '1.234568e+02',
        '-1.234568e+03',
        '1.234568e+04',
        '-1.234568e+05',
        '1.234568e+06',
        '-1.234568e+07',
        '1.234568e+08',
        '-1.234568e+08',
        '1.000000e+00',
        '1.000000e+01',
        '1.000000e+02',
        '1.000000e+03',
        '1.000000e+04',
        '1.000000e+05',
        '1.000000e+06',
        '1.000000e+07',
        '1.000000e+08',
        '1.000000e+09',
        '1.000000e-01',
        '1.000000e-02',
        '1.000000e-03',
        '1.000000e-04',
        '1.000000e-05',
        '1.000000e-06',
        '1.000000e-07',
        '1.000000e-08',
        '1.000000e-09',
    ]
    self.Run(_FLOAT_RESOURCE, None, resource_transform.TransformFloat, [],
             expected, kwargs={'spec': 'e'})

  def testTransformFloatWithSpec1F(self):
    expected = [
        '0.0',
        '-0.0',
        '0.0',
        '-0.0',
        '0.0',
        '-0.0',
        '0.1',
        '-0.9',
        '1.0',
        '-1.0',
        '1.0',
        '-1.0',
        '1.0',
        '-1.0',
        '1.0',
        '-1.1',
        '1.9',
        '-1.3',
        '1.7',
        '-12.3',
        '123.5',
        '-1234.6',
        '12345.7',
        '-123456.8',
        '1234567.9',
        '-12345678.9',
        '123456789.0',
        '-123456789.0',
        '1.0',
        '10.0',
        '100.0',
        '1000.0',
        '10000.0',
        '100000.0',
        '1000000.0',
        '10000000.0',
        '100000000.0',
        '1000000000.0',
        '0.1',
        '0.0',
        '0.0',
        '0.0',
        '0.0',
        '0.0',
        '0.0',
        '0.0',
        '0.0',
    ]
    self.Run(_FLOAT_RESOURCE, None, resource_transform.TransformFloat, [],
             expected, kwargs={'precision': 1, 'spec': 'f'})

  def testTransformFloatUndefined(self):
    resource = ['not a float']
    self.Run(resource, None, resource_transform.TransformFloat, [], [''])

  def testTransformFormat(self):
    self.Run(self._resource, None, resource_transform.TransformFormat,
             ['{0} -- {1}', 'status', 'path'],
             ['PASSED -- /dir/base.suffix',
              'FAILED -- /dir/base',
              'WARNING -- dir/base.suffix',
              'DOWN -- \\dir\\base',
              'UNKNOWN -- base.suffix',
              ' -- ',
              'None -- '])

  def testTransformFormatNoArgs(self):
    resource = ['abc', 123, ['a', 'b', 'c'], None]
    self.Run(resource, None, resource_transform.TransformFormat,
             ['-- {0} --'],
             ['-- abc --',
              '-- 123 --',
              '-- a --',
              '--  --'])

  def testTransformGroup(self):
    self.Run(self._resource, 'group', resource_transform.TransformGroup,
             ['code', 'message'], [
                 '[123: Message for 123.] [456: Message for 456.]'
                 ' [789: Message for 789.]',
                 '[123: Message for 123.]',
                 '[456: Message for 456.]',
                 '[789: Message for 789.]',
                 '[]',
                 '[]',
                 '[]'])

  def testTransformIso(self):
    self.Run(self._resource, 'time', resource_transform.TransformIso, [],
             ['T', 'T', 'T', 'T', 'T', 'T', 'T'])

  def testTransformJoin(self):
    # input, sep, result
    tests = [
        ([1, 2, 3, 4], '/', '1/2/3/4'),
        (['a', 'b'], '/', 'a/b'),
        ('abcd', '/', 'a/b/c/d'),
        (['a', 'b'], '!!', 'a!!b'),
        ([], '/', ''),
        ('', '/', ''),
        (['a', 'b'], 0, ''),
        (123, '/', ''),
    ]

    for r, sep, expected in tests:
      self.assertEqual(resource_transform.TransformJoin(r, sep), expected)

  def testTransformJoinCustomUndefined(self):
    self.assertEqual(resource_transform.TransformJoin(
        '', '/', undefined='foobar'), 'foobar')

  def testTransformSortItem(self):
    # input, result
    tests = [
        ([2, 1, 4, 3], [1, 2, 3, 4]),
        (['b', 'a'], ['a', 'b']),
        ([], []),
        ([1, 2, 3, 4], [1, 2, 3, 4]),
    ]

    for r, expected in tests:
      self.assertEqual(resource_transform.TransformSort(r), expected)

  def testTransformSortWithKey(self):
    obj1 = {
        'foo': {
            'bar': 3,
        },
    }
    obj2 = {
        'foo': {
            'bar': 4,
        },
    }
    self.assertEqual(resource_transform.TransformSort([obj2, obj1], 'foo.bar'),
                     [obj1, obj2])

  def testTransformCountItem(self):
    # input, result
    tests = [
        ([2, 1, 4, 1], {1: 2, 2: 1, 4: 1}),
        (['b', 'a', 'b'], {'a': 1, 'b': 2}),
        ('ababba', {'a': 3, 'b': 3}),
        ([], {}),
    ]

    for r, expected in tests:
      self.assertEqual(resource_transform.TransformCount(r), expected)

  def testTransformCountComplexKeys(self):
    obj1 = {
        'foo': {
            'bar': 3,
        },
    }
    obj2 = {
        'foo': {
            'bar': 4,
        },
    }
    self.assertEqual(resource_transform.TransformCount([obj2, obj1, obj2]), {})

  def testTransformLen(self):
    self.Run(self._resource, 'group', resource_transform.TransformLen, [],
             [3, 1, 1, 1, 0, 0, 0])

  def testTransformListDict(self):
    self.Run(self._resource, 'dict', resource_transform.TransformList, [],
             ['a=1,b=2,c=3,d=4', 'A=a,B=b,C=c,D=d', 'B=b,D=d', '',
              'line of text', 1234, ''])

  def testTransformListDictSemicolon(self):
    kwargs = {'separator': ';', 'undefined': 'EMPTY'}
    self.Run(self._resource, 'dict', resource_transform.TransformList, [],
             ['a=1;b=2;c=3;d=4', 'A=a;B=b;C=c;D=d', 'B=b;D=d', 'EMPTY',
              'line of text', 1234, 'EMPTY'], kwargs)

  def testTransformListDictKeys(self):
    kwargs = {'show': 'keys'}
    self.Run(self._resource, 'dict', resource_transform.TransformList, [],
             ['a,b,c,d', 'A,B,C,D', 'B,D', '', 'line of text', 1234, ''],
             kwargs)

  def testTransformListDictValues(self):
    kwargs = {'show': 'values'}
    self.Run(self._resource, 'dict', resource_transform.TransformList, [],
             ['1,2,3,4', 'a,b,c,d', 'b,d', '', 'line of text', 1234, ''],
             kwargs)

  def testTransformListList(self):
    self.Run(self._resource, 'list', resource_transform.TransformList, [],
             ['1,2,3,4', 'a,b,c,d', '1,b,3,d', '1,2,3,4',
              '1,2,3,4', '1,2,3,4', '1,2,3,4'])

  def testTransformListListSemicolon(self):
    kwargs = {'separator': ';', 'undefined': 'EMPTY'}
    self.Run(self._resource, 'list', resource_transform.TransformList, [],
             ['1;2;3;4', 'a;b;c;d', '1;b;3;d', '1;2;3;4',
              '1;2;3;4', '1;2;3;4', '1;2;3;4'], kwargs)

  def testTransformListNotAList(self):
    self.Run(self._resource, 'value', resource_transform.TransformList, [],
             ['', '', True, '', '1', '', ''])

  def testTransformNotNull(self):
    resource = [
        {
            'list': [1, 2, 3, 4]
        },
        {
            'list': [1, None, 3, None]
        },
        {
            'list': [None, None, None]
        },
        {
            'list': None
        },
        {
            'list': 5
        }
    ]
    self.Run(resource, 'list', resource_transform.TransformNotNull, [], [
        [1, 2, 3, 4],
        [1, 3],
        [],
        [],
        [],
    ])

  def testTransformResolution(self):
    self.Run(self._resource, 'res', resource_transform.TransformResolution,
             ['unknown'],
             ['100 x 200', '100 x 200', '100 x 200', '100 x 200', '100 x 200',
              'unknown', 'unknown'])

  def testTransformScope(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformScope, [],
             ['region-a/foo/bar',
              'zone-b/foo/bar',
              'bar',
              'zone-b/foo/bar',
              'zone-b/foo/bar',
              '',
              'zones'])

  def testTransformScopeWithRegions(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformScope,
             ['regions'],
             ['region-a/foo/bar',
              'bar',
              'bar',
              'bar',
              'bar',
              '',
              'zones'])

  def testTransformScopeWithProjectsAndZones(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformScope,
             ['projects', 'zones'],
             ['bar',
              'zone-b/foo/bar',
              'project-c/foo/bar',
              'zone-b/foo/bar',
              'zone-b/foo/bar',
              '',
              'zones'])

  def testTransformScopeNoHttps(self):
    self.Run(self._resource, 'path', resource_transform.TransformScope,
             ['projects', 'zones'],
             ['/dir/base.suffix',
              '/dir/base',
              'dir/base.suffix',
              '\\dir\\base',
              'base.suffix',
              '',
              ''])

  def testTransformSegment(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [],
             ['bar',
              'bar',
              'bar',
              'bar',
              'bar',
              '',
              'zones'])

  def testTransformSegmentNotLink(self):
    self.Run(self._resource, 'status', resource_transform.TransformSegment,
             [],
             ['PASSED', 'FAILED', 'WARNING', 'DOWN', 'UNKNOWN', '', ''])

  def testTransformSegment0(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [0],
             ['https:',
              'https:',
              'https:',
              'https:',
              'https:',
              'https:',
              'https:'])

  def testTransformSegment1(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [1],
             ['',
              '',
              '',
              '',
              '',
              '',
              ''])

  def testTransformSegment2(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [2],
             ['oo',
              'oo',
              'oo',
              'oo',
              'oo',
              'oo',
              'oo'])

  def testTransformSegment4(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [4],
             ['regions',
              'zones',
              'projects',
              'zones',
              'zone',
              'zones',
              'zones'])

  def testTransformSegment9(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformSegment,
             [9],
             ['',
              '',
              '',
              'bar',
              'bar',
              '',
              ''])

  def testTransformSize(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1.0 TiB', '1.0 GiB', '1.1 MiB', '1.1 KiB', '123 bytes', '-',
              '1.0 PiB'])

  def testTransformSizeWithUnitInSuffix(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1.0 PiB', '1.0 TiB', '1.1 GiB', '1.1 MiB', '123 KiB', '-',
              '1.0 PiB'],
             kwargs={'units_in': 'K'},
            )

  def testTransformSizeWithUnitInSize(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1000.0 TiB',
              '1000.1 GiB',
              '1.1 GiB',
              '1.1 MiB',
              '120.1 KiB',
              '-',
              '1000.0 PiB'],
             kwargs={'units_in': 1000.0},
            )

  def testTransformSizeWithUnitOutSuffix(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1024.0', '1.0', '0.0', '0.0', '0.0', '-', '1048576.0'],
             kwargs={'units_out': 'G'},
            )

  def testTransformSizeWithUnitOutSize(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1.0 TiB', '1.0 GiB', '1.1 MiB', '1.1 KiB', '123 bytes', '-',
              '1.0 PiB'],
             kwargs={'units_out': 2 ** 20},
            )

  def testTransformSizeWithPrecision(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1.00 TiB', '1.00 GiB', '1.12 MiB', '1.12 KiB', '123 bytes',
              '-', '1.00 PiB'],
             kwargs={'precision': 2},
            )

  def testTransformSizeWithPrecisionString(self):
    self.Run(self._resource, 'size', resource_transform.TransformSize,
             ['-'],
             ['1.00 TiB', '1.00 GiB', '1.12 MiB', '1.12 KiB', '123 bytes',
              '-', '1.00 PiB'],
             kwargs={'precision': '2'},
            )

  def testTransformSizeUndefined(self):
    resource = ['not a float']
    self.Run(resource, None, resource_transform.TransformSize, [], ['0 bytes'])

  def testTransformSlice(self):
    # input, op, result
    tests = [
        ([1, 2, 3, 4], '1', [2]),
        ([1, 2, 3, 4], ' 1 ', [2]),
        ([1, 2, 3, 4], '-1', [4]),
        ([1, 2, 3, 4], ':', [1, 2, 3, 4]),
        ([1, 2, 3, 4], '::', [1, 2, 3, 4]),
        ([1, 2, 3, 4], '1:', [2, 3, 4]),
        ([1, 2, 3, 4], '0:2', [1, 2]),
        ([1, 2, 3, 4], '0:20', [1, 2, 3, 4]),
        ([1, 2, 3, 4], '2:0', ''),
        ([1, 2, 3, 4], '2:0:-1', [3, 2]),
        ([1, 2, 3, 4], '0 : 4 : 1', [1, 2, 3, 4]),
        ([1, 2, 3, 4], '::-1', [4, 3, 2, 1]),
        ([1, 2, 3, 4], ' : : -1', [4, 3, 2, 1]),
        ([1, 2, 3, 4], '20', ''),
        ([1, 2, 3, 4], '20:', ''),
        ([1, 2, 3, 4], '::0', ''),  # step can't be 0
        ([1, 2, 3, 4], '1:2:3:4', ''),  # op can't have > 3 colons
        ([1, 2, 3, 4], 'a', ''),
        ([1, 2, 3, 4], 'a:b:c', ''),
        ([1, 2, 3, 4], '', ''),
        ([1, 2, 3, 4], '  ', ''),
        ('abcd', '1', ['b']),
        ('abcd', ':', ['a', 'b', 'c', 'd']),
        ((1, 2, 3, 4), '1', [2]),
        ((1, 2, 3, 4), ':', [1, 2, 3, 4]),
        ({1: 1}, '0', ''),
    ]

    for r, op, expected in tests:
      self.assertEqual(resource_transform.TransformSlice(r, op), expected)

  def testTransformSliceCustomUndefined(self):
    self.assertEqual(resource_transform.TransformSlice(
        [1, 2, 3, 4], '20:', undefined='foobar'), 'foobar')

  def testTransformSplit(self):
    # input, sep, result
    tests = [
        ('a/b/c/d', '/', ['a', 'b', 'c', 'd']),
        ('a/b!!c/d', '!!', ['a/b', 'c/d']),
        ('', '/', ''),
        ('abcd', '', ''),
        ('abcd', 0, ''),
        (1234, '/', ''),
    ]

    for r, sep, expected in tests:
      self.assertEqual(resource_transform.TransformSplit(r, sep), expected)

  def testTransformSplitCustomUndefined(self):
    self.assertEqual(resource_transform.TransformSplit(
        '', '/', undefined='foobar'), 'foobar')

  def testTransformSub(self):
    # input, pattern, replacement, result, kwargs
    tests = [
        # Check that matching is case-insensitive by default.
        ('My name is jen', 'Jen', 'Bob', 'My name is Bob', {}),
        # Check that matching can be manually set to case-insensitive.
        ('My name is jen', 'Jen', 'Bob', 'My name is Bob', {'ignorecase': '1'}),
        # Check that we can disable ignorecase.
        ('Jen is jen', 'jen', 'Bob', 'Jen is Bob', {'ignorecase': '0'}),
        # Check that multi-line matching works.
        ('two\nlines', '^lines', 'words', 'two\nwords', {}),
        # Check that the dot matches across lines.
        ('A spans\n3\nlines', 'spans.*', 'is one line', 'A is one line', {}),
        # Don't replace anything when there's no match.
        ('some string', 'doesnt exist', 'stuff', 'some string', {}),
        # Check that we can limit the number of replacements.
        ('bye bye', 'bye', 'hello', 'hello bye', {'count': '1'}),
        # Check that the original string is returned when invalid regexp passed.
        ('some(str', '(str', '', 'some(str', {}),
    ]

    for r, pattern, replacement, expected, kwargs in tests:
      self.assertEqual(
          resource_transform.TransformSub(r, pattern, replacement, **kwargs),
          expected)

  def testTransformUri(self):
    self.Run(self._resource, None, resource_transform.TransformUri, [],
             ['https://oo/before/regions/region-a/foo/bar',
              'https://oo/before/zones/zone-b/foo/bar',
              'https://oo/before/projects/project-c/foo%2Fbar',
              'https://oo/before/zones/all/zones/zone-b/foo/bar',
              'https://oo/before/zone/all/zones/zone-b/foo%2Fbar',
              'https://oo/before/zones/',
              'https://oo/before/zones'])

  def testTransformUriValue(self):
    self.Run(self._resource, 'selfLink', resource_transform.TransformUri, [],
             ['https://oo/before/regions/region-a/foo/bar',
              'https://oo/before/zones/zone-b/foo/bar',
              'https://oo/before/projects/project-c/foo%2Fbar',
              'https://oo/before/zones/all/zones/zone-b/foo/bar',
              'https://oo/before/zone/all/zones/zone-b/foo%2Fbar',
              'https://oo/before/zones/',
              'https://oo/before/zones'])

  def testTransformUriSelfLink1(self):
    self.Run([self.SelfLink1()], None, resource_transform.TransformUri, [],
             ['https://oo/selfLink1'])

  def testTransformUriSelfLink2(self):
    self.Run([self.SelfLink2()], None, resource_transform.TransformUri, [],
             ['https://oo/SelfLink2'])

  def testTransformYesNo(self):
    self.Run(self._resource, 'value', resource_transform.TransformYesNo,
             ['set', 'empty'],
             ['empty', 'empty', 'set', 'empty', 'set', 'empty', 'empty'])

  def testTransformYesNoDefault(self):
    self.Run(self._resource, 'value', resource_transform.TransformYesNo,
             [],
             ['No', 'No', True, 'No', [1], 'No', 'No'])

  def testTransformYesNoYes(self):
    self.Run(self._resource, 'value', resource_transform.TransformYesNo,
             ['Yes'],
             ['No', 'No', 'Yes', 'No', 'Yes', 'No', 'No'])

  def testTransformYesNo10(self):
    self.Run(self._resource, 'value', resource_transform.TransformYesNo,
             ['1', '0'],
             ['0', '0', '1', '0', '1', '0', '0'])

  def testTransformYesNoValueUnset(self):
    self.Run(self._resource, 'value', resource_transform.TransformYesNo,
             [None, 'unset'],
             ['unset', 'unset', True, 'unset', [1], 'unset', 'unset'])


class ResourceTransformMockRegistryTest(test_case.Base):

  _MOCK_API_TO_TRANSFORMS = {
      'known': (
          'googlecloudsdk.core.resource.resource_transform',
          'GetTransforms'
      ),
      'module': (
          'bad.module.path',
          'GetTransforms'
      ),
      'method': (
          'googlecloudsdk.core.resource.resource_transform',
          'BadMethodName'
      ),
  }

  def SetUp(self):
    self.StartObjectPatch(
        resource_transform, '_API_TO_TRANSFORMS', self._MOCK_API_TO_TRANSFORMS)

  def testTransformRegistryKnownCollection(self):
    expected = resource_transform.GetTransforms()
    actual = resource_transform.GetTransforms('known.foo')
    self.assertEqual(expected, actual)

  def testTransformRegistryUnknownCollection(self):
    expected = None
    actual = resource_transform.GetTransforms('unknown.foo')
    self.assertEqual(expected, actual)

  def testTransformRegistryBadModulePath(self):
    with self.assertRaises(ImportError):
      resource_transform.GetTransforms('module.bad.path')

  def testTransformRegistryBadMethodName(self):
    with self.assertRaises(AttributeError):
      resource_transform.GetTransforms('method.bad.name')


class ResourceTransformRealRegistryTest(test_case.Base):

  def testTransformRegistryDefaultBuiltins(self):
    transforms = resource_transform.GetTransforms()
    expected = [
        'always',
        'basename',
        'collection',
        'color',
        'count',
        'date',
        'decode',
        'duration',
        'encode',
        'enum',
        'error',
        'extract',
        'fatal',
        'firstof',
        'float',
        'format',
        'group',
        'if',
        'iso',
        'join',
        'len',
        'list',
        'map',
        'notnull',
        'resolution',
        'scope',
        'segment',
        'size',
        'slice',
        'sort',
        'split',
        'sub',
        'synthesize',
        'uri',
        'yesno',
    ]
    self.assertEqual(expected, sorted(transforms.keys()))

  def testTransformRegistryExplicitBuiltins(self):
    expected = resource_transform.TransformBaseName
    actual = resource_transform.GetTransforms('builtin').get('basename', None)
    self.assertEqual(expected, actual)

  def testTransformRegistryCompute(self):
    transforms = resource_transform.GetTransforms('compute.instances')
    expected = [
        'firewall_rule',
        'image_alias',
        'location',
        'location_scope',
        'machine_type',
        'name',
        'next_maintenance',
        'operation_http_status',
        'project',
        'quota',
        'scoped_suffixes',
        'status',
        'type_suffix',
        'zone'
    ]
    self.assertEqual(expected, sorted(transforms.keys()))


class ResourceTransformUtilTest(test_case.Base):

  def testGetBooleanArgValue(self):
    self.assertTrue(resource_transform.GetBooleanArgValue('True'))
    self.assertTrue(resource_transform.GetBooleanArgValue('TRUE'))
    self.assertTrue(resource_transform.GetBooleanArgValue('true'))
    self.assertTrue(resource_transform.GetBooleanArgValue('foo'))
    self.assertTrue(resource_transform.GetBooleanArgValue(1))
    self.assertTrue(resource_transform.GetBooleanArgValue(3.14))

    self.assertFalse(resource_transform.GetBooleanArgValue('False'))
    self.assertFalse(resource_transform.GetBooleanArgValue('FALSE'))
    self.assertFalse(resource_transform.GetBooleanArgValue('false'))
    self.assertFalse(resource_transform.GetBooleanArgValue(0))
    self.assertFalse(resource_transform.GetBooleanArgValue(0.0))
    self.assertFalse(resource_transform.GetBooleanArgValue(None))


if __name__ == '__main__':
  test_case.main()

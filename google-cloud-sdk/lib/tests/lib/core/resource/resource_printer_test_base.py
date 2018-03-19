# -*- coding: utf-8 -*-
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

"""Base test module for the resource_printer tests."""

from __future__ import absolute_import
from __future__ import division
import collections

from googlecloudsdk.core.resource import resource_printer
from tests.lib import sdk_test_base

import six
from six.moves import range  # pylint: disable=redefined-builtin


class _Quote(object):
  """A test quote object."""

  def __init__(self, index):
    self.a = index
    self.b = '{0}.{1}'.format(index, index + 1)


class _ObjectResource(object):
  """An object resource to test column format serialization."""

  def __init__(self, index=0):
    self.name = 'B{0}'.format(index)
    self.quote = _Quote(index)
    self.id = index


class Base(sdk_test_base.WithOutputCapture):
  """A Base module for the resource_printer tests."""

  def SetUp(self):
    self.text_resource = {
        'a': 'no leading or trailing space',
        'b': '  leading space',
        'c': 'trailing space  ',
        'd': '  surrounded by space  ',
        'e': ' Leading space.\nTrailing space.  \n  Leading and Trailing.  ',
        'f': 'This is the first line.\nAnd the middle line.\nFinally at last.',
    }
    self.float_resource = {
        'a': 1.00000009,
        'b': -1.0000009,
        'c': 1.000009,
        'd': -1.00009,
        'e': 1.0009,
        'f': -1.009,
        'g': 1.009,
        'h': -1.09,
        'i': 1.9,
        'j': -1.3333333,
        'k': 1.6666666,
        'l': -12.345678901,
        'm': 123.45678901,
        'n': -1234.5678901,
        'o': 12345.678901,
        'p': -123456.78901,
        'q': 1234567.8901,
        'r': -12345678.901,
        's': 123456789.01,
        't': -1234567890.123456789,
    }
    self.none_dict_resource = [
        {
            'a': None,
            'n': 'nnn',
            'z': 'xyz',
        },
        {
            'a': 'abc',
            'n': None,
            'z': 'xyz',
        },
        {
            'a': None,
            'n': None,
            'z': None,
        },
    ]
    self.none_list_resource = [
        [
            None,
            'nnn',
            'xyz',
        ],
        [
            'abc',
            None,
            'xyz',
        ],
        [
            None,
            None,
            None,
        ],
    ]
    self.ordered_dict_resource = [
        collections.OrderedDict([
            (u'allowed', [
                collections.OrderedDict([
                    (u'IPProtocol', u'tcp'),
                    (u'ports', [u'2376'])
                ])
            ]),
            (u'creationTimestamp', u'2015-05-20T08:14:24.654-07:00'),
            (u'description', u''),
            (u'id', u'123456789'),
            (u'kind', u'compute#firewall'),
            (u'name', u'allow-gae-builder'),
            (u'network', u'default'),
            (u'sourceRanges', [u'0.0.0.0/0'])
        ])
    ]
    self.repeated_resource = [
        {
            'selfLink': '/1/2/3/4/5',
        },
        {
            'selfLink': '/i/ii/iii/iv/v/vi',
        },
        {
            'selfLink': '/I/II/III/IV/V/VI',
        },
    ]
    self.width_resource = [
        {
            'head': 'zero',
            'data': u':\N{ZERO WIDTH SPACE}\N{SOFT HYPHEN}:',
            'tail': 'ZERO',
        },
        {
            'head': 'one',
            'data': u':Ü:',
            'tail': 'ONE',
        },
        {
            'head': 'two',
            'data': u':車:',
            'tail': 'TWO',
        },
    ]
    self.multiline_width_resource = [
        {
            'head': 'zero',
            'data': u':{lotsofzerodata}:'.format(
                lotsofzerodata=u'\N{ZERO WIDTH SPACE}\N{SOFT HYPHEN}' * 64),
            'tail': 'ZERO',
        },
        {
            'head': 'one',
            'data': u':{lotsofonedata}:'.format(
                lotsofonedata=u'Ü' * 64),
            'tail': 'ONE',
        },
        {
            'head': 'two',
            'data': u':{lotsoftwodata}:'.format(
                lotsoftwodata=u'車' * 64),
            'tail': 'TWO',
        },
    ]
    self.unicode_key_resource = [
        {
            u'ħɇȺđ': 'zero',
            u'∂αтα': u':\N{ZERO WIDTH SPACE}\N{SOFT HYPHEN}:',
            u'ẗäïḷ': 'ZERO',
        },
        {
            u'ħɇȺđ': 'one',
            u'∂αтα': u':Ü:',
            u'ẗäïḷ': 'ONE',
        },
        {
            u'ħɇȺđ': 'two',
            u'∂αтα': u':車:',
            u'ẗäïḷ': 'TWO',
        },
    ]

  @staticmethod
  def CreateResourceList(num):
    """Creates a list of resources.

    Args:
      num: The number of elements in the resource list.

    Yields:
      The resource list.
    """
    for i in range(num):
      yield {
          'name': u'my-instance-a{0}-{1}'.format('z' * i, i),
          'SelfLink': u'http://g/selfie/a{0}-{1}'.format('z' * i, i),
          'kind': 'compute#instance',
          'labels': {
              'empty': '',
              'full': 'value',
              u'Ṳᾔḯ¢◎ⅾℯ': u'®ǖɬɘς',
          },
          'networkInterfaces': [
              {
                  'accessConfigs': [
                      {
                          'kind': 'compute#accessConfig',
                          'type': 'ONE_TO_ONE_NAT',
                          'name': 'External NAT',
                          'natIP': '74.125.239.110',
                          },
                      ],
                  'networkIP': '10.240.150.{0}'.format(i),
                  'name': 'nic0',
                  'network': 'default',
                  },
              ],
          'metadata': {
              'kind': 'compute#metadata.{0}'.format((1001 - i) % 3),
              'items': [
                  {'key': 'a', 'value': 'b'},
                  {'key': 'c', 'value': 'd'},
                  {'key': 'e', 'value': 'f'},
                  {'key': 'g', 'value': 'h'},
                  ],
              },
          'unicode': u'python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ',
          }

  @staticmethod
  def CreateObjectResourceList(num):
    """Creates a list of object resources.

    Args:
      num: The number of elements in the resource list.

    Yields:
      The resource list.
    """
    for i in range(num):
      yield _ObjectResource(i)

  def Print(self, style='table', attributes='', fields=None, count=None,
            heading=None, resource=None, encoding=None):
    """Prints an example resource.

    Args:
      style: The format style name. For 'list' the resource is a list of names,
        otherwise the resource is a list of dicts.
      attributes: The ,-separated list of [no-]name[=value] attributes.
      fields: The field projection expression.
      count: The number of resource records to print.
      heading: The list of heading strings.
      resource: resource override.
      encoding: If not None then top level unicode keys and values in the
        resource are encoded using this encoding.
    """
    if resource is None:
      if style == 'list':
        resource = [
            u'Ṁöë',
            'Larry',
            'Shemp',
            'Curly',
            'Joe',
            'Curly Joe',
        ]
      elif 'utf8' in attributes.split(',') or 'win' in attributes.split(','):
        resource = [
            {'name': 'Moe', 'kind': 'aaa', 'id': 1267},
            {'name': 'Larry', 'kind': 'xxx', 'id': 1245},
            {'name': 'Shemp', 'kind': 'xxx', 'id': 1233},
            {'name': 'Curly', 'kind': 'qqq', 'id': 1234},
            {'name': 'Joe', 'kind': ['new', 1], 'id': ['x', 6789]},
            {'name': 'Curly Joe',
             'kind': {'new': 2, 'a': 'b', 'q': 'a,z'}, 'id': {'x': 890}},
        ]
        if fields is None:
          fields = '(name, kind, id)'
      else:
        resource = [
            {
                'name': u'Ṁöë',
                'quote': u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW",
                'id': 1267,
            },
            {
                'name': 'Larry',
                'quote': u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",
                'id': 1245,
            },
            {
                'name': 'Shemp',
                'quote': u'Hey, Ṁöë! Hey, Larry!',
                'id': 'lrlrlrl',
            },
            {
                'name': 'Curly',
                'quote': u'Søɨŧɇnłɏ!',
                'id': 1234,
            },
            {
                'name': 'Joe',
                'quote': 'Oh, cut it ouuuuuut!',
                'id': ['new', 6789],
            },
            {
                'name': 'Curly Joe',
                'quote': "One of these days, you're gonna poke my eyes out.",
                'id': {'new': 890},
            },
        ]
        # This branch is flagged by mutant analysis. If it is omitted no tests
        # fail. This is because the code under test handles encoded data by
        # design. If a test were to fail here, either with or without encoding,
        # that would mean a bug in the code under test.
        if encoding:
          encoded_resource = []
          for r in resource:
            item = {}
            for k, v in six.iteritems(r):
              if isinstance(k, six.text_type):
                k = k.encode(encoding)
              if isinstance(v, six.text_type):
                v = v.encode(encoding)
              item[k] = v
            encoded_resource.append(item)
          resource = encoded_resource
      if count is None:
        count = 4
    if fields is None:
      fields = '(name, quote, id)'
    fmt = style + attributes + fields
    printer = resource_printer.Printer(fmt)
    if heading:
      printer.AddHeading(heading)
    if count is not None:
      resource = resource[:count]
    for record in resource:
      printer.AddRecord(record)
    printer.Finish()


def main():
  return sdk_test_base.main()

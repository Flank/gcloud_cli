# -*- coding: utf-8 -*- #
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

"""Unit tests for the resource_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import encoding
from tests.lib.core.resource import resource_printer_test_base


_RESOURCE_NESTED_LIST = [
    {
        'abc': [
            {
                'def': [
                    {
                        'ghi': [
                            1,
                            2,
                        ],
                    },
                    {
                        'ghi': [
                            3,
                            4,
                        ],
                    },
                ],
            },
            {
                'def': [
                    {
                        'ghi': [
                            5,
                            6,
                        ],
                    },
                    {
                        'ghi': [
                            7,
                            8,
                        ],
                    },
                ],
            },
        ],
    },
]


class ResourcePrinterTransformTest(resource_printer_test_base.Base):

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
      # common_typos_disable
      self.selfLink = 'https://oo/selfLink'  # pylint: disable=invalid-name
      # common_typos_enable

  class SelfLink2(object):

    def __init__(self):
      # common_typos_disable
      self.SelfLink = 'https://oo/SelfLink'  # pylint: disable=invalid-name
      # common_typos_enable

  def SetUp(self):
    self._resource = [
        {
            'path': '/dir/base.suffix',
            'time': self.Time(12345678),
            'list': [1, 2, 3, 4],
            'res': self.Resolution1(100, 200),
            'size': 1024 * (1024 * 1024 * 1024 + 123),
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'PASS',
            'value': None,
            },
        {
            'path': '/dir/base',
            'time': self.Time(23456789),
            'list': ['a', 'b', 'c', 'd'],
            'res': self.Resolution2(100, 200),
            'size': 1024 * (1024 * 1024 + 123),
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'OK',
            'value': 0,
            },
        {
            'path': 'dir/base.suffix',
            'time': self.Time(34567890),
            'list': [1, 'b', 3, 'd'],
            'res': self.Resolution3(100, 200),
            'size': 1024 * (1024 + 123),
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'FAIL',
            'value': True,
            },
        {
            'path': 'dir/base',
            'time': self.Time(45678901),
            'list': [1, 2, 3, 4],
            'res': self.Resolution4(100, 200),
            'size': 1024 + 123,
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'ERROR',
            'value': [],
            },
        {
            'path': 'base.suffix',
            'time': self.Time(56789012),
            'list': [1, 2, 3, 4],
            'res': self.Resolution5(100, 200),
            'size': 123,
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'WARNING',
            'value': [1],
            },
        {
            'path': '',
            'time': self.Time(67890123),
            'list': [1, 2, 3, 4],
            'res': self.Resolution6(100, 200),
            'size': 0,
            'selfLink': 'https://oo/uri',  # NOTYPO
            'status': 'UNKNOWN',
            'value': '',
            },
        ]

  def Print(self, style='table', projection=None, attr=None, resource=None):
    if not projection:
      projection = ('('
                    'path.basename(), '
                    'time.iso(), '
                    'list.list(), '
                    'res.resolution(unknown):label=RESOLUTION, '
                    'size.size(-), '
                    'uri(), '
                    'value.yesno(set, empty))')
    fmt = style + projection
    if attr:
      fmt += attr
    printer = resource_printer.Printer(fmt)
    for record in resource or self._resource:
      printer.AddRecord(record)
    printer.Finish()

  def testTableTransform(self):
    self.Print()
    # common_typos_disable
    self.AssertOutputEquals(textwrap.dedent("""\
    PATH         TIME  LIST     RESOLUTION  SIZE       URI             VALUE
    base.suffix  T     1,2,3,4  100 x 200   1.0 TiB    https://oo/uri  empty
    base         T     a,b,c,d  100 x 200   1.0 GiB    https://oo/uri  empty
    base.suffix  T     1,b,3,d  100 x 200   1.1 MiB    https://oo/uri  set
    base         T     1,2,3,4  100 x 200   1.1 KiB    https://oo/uri  empty
    base.suffix  T     1,2,3,4  100 x 200   123 bytes  https://oo/uri  set
                 T     1,2,3,4  unknown     -          https://oo/uri  empty
        """))
    # common_typos_enable

  def testTableTransformResolution(self):
    self.Print(projection='(res.resolution(undefined=unknown):label="X x Y")')
    self.AssertOutputEquals(textwrap.dedent("""\
    X x Y
    100 x 200
    100 x 200
    100 x 200
    100 x 200
    100 x 200
    unknown
        """))

  def testTableTransformResolutionTranspose(self):
    self.Print(projection=
               '(res.resolution(undefined=unknown,transpose=1):label="Y x X")')
    self.AssertOutputEquals(textwrap.dedent("""\
    Y x X
    200 x 100
    200 x 100
    200 x 100
    200 x 100
    200 x 100
    unknown
        """))

  def testTableTransformColor(self):
    self.StartEnvPatch({})
    encoding.SetEncodedValue(os.environ, 'TERM', 'xterm')
    console_attr.GetConsoleAttr('utf8', reset=True)

    self.Print(projection='(status.color(red=FAIL|ERROR,yellow=WARNING,'
               'green=PASS|OK):label=STATUS)')
    self.AssertOutputEquals(textwrap.dedent("""\
    STATUS
    \x1b[32mPASS   \x1b[39;0m
    \x1b[32mOK     \x1b[39;0m
    \x1b[31;1mFAIL   \x1b[39;0m
    \x1b[31;1mERROR  \x1b[39;0m
    \x1b[33;1mWARNING\x1b[39;0m
    UNKNOWN
        """))

  def testJsonDefaultTransforms(self):
    self.Print(style='json')
    self.maxDiff = None  # pylint: disable=invalid-name
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "list": "1,2,3,4",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "1.0 TiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "a,b,c,d",
            "path": "base",
            "res": "100 x 200",
            "size": "1.0 GiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "1,b,3,d",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "1.1 MiB",
            "time": "T",
            "value": "set"
          },
          {
            "list": "1,2,3,4",
            "path": "base",
            "res": "100 x 200",
            "size": "1.1 KiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "1,2,3,4",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "123 bytes",
            "time": "T",
            "value": "set"
          },
          {
            "list": "1,2,3,4",
            "path": "",
            "res": "unknown",
            "size": "-",
            "time": "T",
            "value": "empty"
          }
        ]
        """))

  def testJsonDefaultTransformsNoProjection(self):
    self.Print(style='json', projection=' ')
    self.maxDiff = None
    # common_typos_disable
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "/dir/base.suffix",
            "res": {
              "height": 200,
              "width": 100
            },
            "selfLink": "https://oo/uri",
            "size": 1099511753728,
            "status": "PASS",
            "time": {},
            "value": null
          },
          {
            "list": [
              "a",
              "b",
              "c",
              "d"
            ],
            "path": "/dir/base",
            "res": {
              "col": 100,
              "row": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1073867776,
            "status": "OK",
            "time": {},
            "value": 0
          },
          {
            "list": [
              1,
              "b",
              3,
              "d"
            ],
            "path": "dir/base.suffix",
            "res": {
              "col": 100,
              "line": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1174528,
            "status": "FAIL",
            "time": {},
            "value": true
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "dir/base",
            "res": {
              "screenx": 100,
              "screeny": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1147,
            "status": "ERROR",
            "time": {},
            "value": []
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "base.suffix",
            "res": {
              "x": 100,
              "y": 200
            },
            "selfLink": "https://oo/uri",
            "size": 123,
            "status": "WARNING",
            "time": {},
            "value": [
              1
            ]
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "",
            "res": {
              "bar": 200,
              "foo": 100
            },
            "selfLink": "https://oo/uri",
            "size": 0,
            "status": "UNKNOWN",
            "time": {},
            "value": ""
          }
        ]
        """))
    # common_typos_enable

  def testJsonDefaultNoTransforms(self):
    self.Print(style='json[no-transforms]')
    self.maxDiff = None
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "/dir/base.suffix",
            "res": {
              "height": 200,
              "width": 100
            },
            "size": 1099511753728,
            "time": {},
            "value": null
          },
          {
            "list": [
              "a",
              "b",
              "c",
              "d"
            ],
            "path": "/dir/base",
            "res": {
              "col": 100,
              "row": 200
            },
            "size": 1073867776,
            "time": {},
            "value": 0
          },
          {
            "list": [
              1,
              "b",
              3,
              "d"
            ],
            "path": "dir/base.suffix",
            "res": {
              "col": 100,
              "line": 200
            },
            "size": 1174528,
            "time": {},
            "value": true
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "dir/base",
            "res": {
              "screenx": 100,
              "screeny": 200
            },
            "size": 1147,
            "time": {},
            "value": []
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "base.suffix",
            "res": {
              "x": 100,
              "y": 200
            },
            "size": 123,
            "time": {},
            "value": [
              1
            ]
          },
          {
            "list": [
              1,
              2,
              3,
              4
            ],
            "path": "",
            "res": {
              "bar": 200,
              "foo": 100
            },
            "size": 0,
            "time": {},
            "value": ""
          }
        ]
        """))

  def testJsonTransforms(self):
    self.Print(style='json[transforms]')
    self.maxDiff = None
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "list": "1,2,3,4",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "1.0 TiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "a,b,c,d",
            "path": "base",
            "res": "100 x 200",
            "size": "1.0 GiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "1,b,3,d",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "1.1 MiB",
            "time": "T",
            "value": "set"
          },
          {
            "list": "1,2,3,4",
            "path": "base",
            "res": "100 x 200",
            "size": "1.1 KiB",
            "time": "T",
            "value": "empty"
          },
          {
            "list": "1,2,3,4",
            "path": "base.suffix",
            "res": "100 x 200",
            "size": "123 bytes",
            "time": "T",
            "value": "set"
          },
          {
            "list": "1,2,3,4",
            "path": "",
            "res": "unknown",
            "size": "-",
            "time": "T",
            "value": "empty"
          }
        ]
        """))

  def testJsonSomeAlwaysTransform(self):
    self.Print(style='table', attr=':(list.always().list()) json')
    self.maxDiff = None
    # common_typos_disable
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "list": "1,2,3,4",
            "path": "/dir/base.suffix",
            "res": {
              "height": 200,
              "width": 100
            },
            "selfLink": "https://oo/uri",
            "size": 1099511753728,
            "status": "PASS",
            "time": {},
            "value": null
          },
          {
            "list": "a,b,c,d",
            "path": "/dir/base",
            "res": {
              "col": 100,
              "row": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1073867776,
            "status": "OK",
            "time": {},
            "value": 0
          },
          {
            "list": "1,b,3,d",
            "path": "dir/base.suffix",
            "res": {
              "col": 100,
              "line": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1174528,
            "status": "FAIL",
            "time": {},
            "value": true
          },
          {
            "list": "1,2,3,4",
            "path": "dir/base",
            "res": {
              "screenx": 100,
              "screeny": 200
            },
            "selfLink": "https://oo/uri",
            "size": 1147,
            "status": "ERROR",
            "time": {},
            "value": []
          },
          {
            "list": "1,2,3,4",
            "path": "base.suffix",
            "res": {
              "x": 100,
              "y": 200
            },
            "selfLink": "https://oo/uri",
            "size": 123,
            "status": "WARNING",
            "time": {},
            "value": [
              1
            ]
          },
          {
            "list": "1,2,3,4",
            "path": "",
            "res": {
              "bar": 200,
              "foo": 100
            },
            "selfLink": "https://oo/uri",
            "size": 0,
            "status": "UNKNOWN",
            "time": {},
            "value": ""
          }
        ]
        """))
    # common_typos_enable

  def testTableTransformFormat(self):
    self.Print(projection='(list.format("{0} => {1}", [0], [1]):label=STATE)')
    self.AssertOutputEquals(textwrap.dedent("""\
        STATE
        1 => 2
        a => b
        1 => b
        1 => 2
        1 => 2
        1 => 2
        """))

  def testTableTransformMap(self):
    self.Print(projection='(list.map().len().list())')
    self.AssertOutputEquals(textwrap.dedent("""\
        LIST
        0,0,0,0
        1,1,1,1
        0,1,0,1
        0,0,0,0
        0,0,0,0
        0,0,0,0
        """))

  def testTableTransformMapStar(self):
    self.Print(projection='(list.*len().list())')
    self.AssertOutputEquals(textwrap.dedent("""\
        LIST
        0,0,0,0
        1,1,1,1
        0,1,0,1
        0,0,0,0
        0,0,0,0
        0,0,0,0
        """))

  def testTableTransformMapNestedList(self):
    self.Print(projection='(abc[].def[].ghi[].map().list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputMatches(textwrap.dedent("""\
        GHI
        \\[u?'\\[1, 2],\\[3, 4]', u?'\\[5, 6],\\[7, 8]']
        """))

  def testTableTransformMapNestedListStar(self):
    self.Print(projection='(abc[].def[].ghi[].*list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputMatches(textwrap.dedent("""\
        GHI
        \\[u?'\\[1, 2],\\[3, 4]', u?'\\[5, 6],\\[7, 8]']
        """))

  def testTableTransformMapNestedList0(self):
    self.Print(projection='(abc[].def[].ghi[].map(0).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [[1, 2], [3, 4]],[[5, 6], [7, 8]]
        """))

  def testTableTransformMapNestedList1(self):
    self.Print(projection='(abc[].def[].ghi[].map(1).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputMatches(textwrap.dedent("""\
        GHI
        \\[u?'\\[1, 2],\\[3, 4]', u?'\\[5, 6],\\[7, 8]']
        """))

  def testTableTransformMapNestedList2(self):
    self.Print(projection='(abc[].def[].ghi[].map(2).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputMatches(textwrap.dedent("""\
        GHI
        \\[u?'1,2', u?'3,4', u?'5,6', u?'7,8']
        """))

  def testTableTransformMapNestedList2Star(self):
    self.Print(projection='(abc[].def[].ghi[].**list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputMatches(textwrap.dedent("""\
        GHI
        \\[u?'1,2', u?'3,4', u?'5,6', u?'7,8']
        """))

  def testTableTransformMapNestedList3(self):
    self.Print(projection='(abc[].def[].ghi[].map(3).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformMapNestedList3Star(self):
    self.Print(projection='(abc[].def[].ghi[].***list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformMapNestedList3ImplicitSlice(self):
    self.Print(projection='(abc.def.ghi.map(3).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformMapNestedList3StarImplicitSlice(self):
    self.Print(projection='(abc.def.ghi.***list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformMapNestedList4(self):
    self.Print(projection='(abc[].def[].ghi[].map(4).list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformMapNestedList4Star(self):
    self.Print(projection='(abc[].def[].ghi[].****list())',
               resource=_RESOURCE_NESTED_LIST)
    self.AssertOutputEquals(textwrap.dedent("""\
        GHI
        [1, 2, 3, 4, 5, 6, 7, 8]
        """))

  def testTableTransformSelfLink1(self):
    resource = [self.SelfLink1()]
    self.Print(resource=resource)
    # common_typos_disable
    self.AssertOutputEquals(textwrap.dedent("""\
        PATH  TIME  LIST  RESOLUTION  SIZE  URI                  VALUE
              T           unknown     -     https://oo/selfLink  empty
        """))
    # common_typos_enable

  def testTableTransformSelfLink2(self):
    resource = [self.SelfLink2()]
    self.Print(resource=resource)
    # common_typos_disable
    self.AssertOutputEquals(textwrap.dedent("""\
        PATH  TIME  LIST  RESOLUTION  SIZE  URI                  VALUE
              T           unknown     -     https://oo/SelfLink  empty
        """))
    # common_typos_enable

  def testTableTransformYesNoDefault(self):
    self.Print(projection='(value.yesno())')
    self.AssertOutputEquals(textwrap.dedent("""\
    VALUE
    No
    No
    True
    No
    [1]
    No
        """))

  def testTableTransformYesNoYes(self):
    self.Print(projection='(value.yesno(yes=Yes))')
    self.AssertOutputEquals(textwrap.dedent("""\
    VALUE
    No
    No
    Yes
    No
    Yes
    No
        """))

  def testTableTransformYesNo10(self):
    self.Print(projection='(value.yesno(1, 0))')
    self.AssertOutputEquals(textwrap.dedent("""\
    VALUE
    0
    0
    1
    0
    1
    0
        """))

  def testTableTransformYesNoValueUnset(self):
    self.Print(projection='(value.yesno(no=unset))')
    self.AssertOutputEquals(textwrap.dedent("""\
    VALUE
    unset
    unset
    True
    unset
    [1]
    unset
        """))


if __name__ == '__main__':
  resource_printer_test_base.main()

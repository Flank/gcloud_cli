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

import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_printer_base
from tests.lib.core.resource import resource_printer_test_base


class MockPrinter(resource_printer_base.ResourcePrinter):

  def __init__(self, *args, **kwargs):
    super(MockPrinter, self).__init__(*args, **kwargs)
    self._rows = []

  def _AddRecord(self, record, delimit=False):
    self._rows.append(record)

  def Finish(self):
    self._rows.append('Finish')

  def Page(self):
    self._rows.append('Page')

  def GetTestOutput(self):
    return self._rows


class ResourcePrinterTest(resource_printer_test_base.Base):

  def testDefaultFormat(self):
    [resource] = self.CreateResourceList(1)
    resource_printer.Print(resource, 'default')
    self.AssertOutputEquals(textwrap.dedent("""\
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))

  def testNoneFormat(self):
    resources = self.CreateResourceList(2)
    resource_printer.Print(resources, 'none')
    self.AssertOutputEquals('')

  def testDisabledNoNameFormat(self):
    resources = self.CreateResourceList(2)
    resource_printer.Print(resources, '[disabled]')
    self.AssertOutputEquals('')

  def testUnknownFormat(self):
    with self.assertRaisesRegex(
        resource_printer.UnknownFormatError,
        r'Format must be one of .* received \[UnKnOwN\]'):
      resource_printer.Printer('UnKnOwN')

  def testSupportedFormats(self):
    formats = resource_printer.SupportedFormats()
    self.assertTrue('default' in formats)
    self.assertTrue('none' in formats)
    self.assertTrue('yaml' in formats)

  def testGetFormatRegistry(self):
    registry = resource_printer.GetFormatRegistry()
    self.assertTrue('default' in registry)
    self.assertTrue('none' in registry)
    self.assertTrue('yaml' in registry)

  def testGetSupportedFormatsAndFormatRegistry(self):
    expected = resource_printer.SupportedFormats()
    registry = resource_printer.GetFormatRegistry()
    actual = sorted(registry)
    self.assertEqual(expected, actual)

  def testDebugAttributeNoProjection(self):
    resources = []
    resource_printer.Print(resources, 'default[debug]')
    self.AssertOutputEquals('')
    self.AssertErrEquals('default format projection:\n')

  def testDebugAttributeWithProjection(self):
    resources = []
    resource_printer.Print(resources,
                           'table[debug](a:sort=1, b.x:sort=2:reverse)')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
table format projection:
   a : (2, 1, 'A', left, None, False, None)
   b : (1, UNORDERED, None, left, None, None, None)
     x : (2, 2, 'X', left, None, False, None, [reverse])
""")

  def testIsResourceMarker(self):
    resource = [[1, 2, 3], ['a', 'b', 'c'],
                resource_printer_base.PageMarker(),
                [7, 8, 9], ['x', 'y', 'z'],
                resource_printer_base.FinishMarker()]
    expected = [False, False, True, False, False, True]
    actual = []
    for record in resource:
      actual.append(resource_printer_base.IsResourceMarker(record))
    self.assertEqual(expected, actual)

  def testFinishMarker(self):
    resource = [[1, 2, 3], ['a', 'b', 'c'],
                resource_printer_base.FinishMarker()]
    expected = [[1, 2, 3], ['a', 'b', 'c'],
                'Finish',
                'Finish']
    printer = MockPrinter()
    printer.Print(resource)
    actual = printer.GetTestOutput()
    self.assertEqual(expected, actual)

  def testFinishPager(self):
    mock_more = self.StartObjectPatch(console_io, 'More')
    resources = []
    resource_printer.Print(resources,
                           'json[pager]')
    mock_more.assert_called_once_with('[]\n', out=log.out)

  def testPageMarker(self):
    resource = [[1, 2, 3], ['a', 'b', 'c'],
                resource_printer_base.PageMarker(),
                [7, 8, 9], ['x', 'y', 'z']]
    expected = [[1, 2, 3], ['a', 'b', 'c'],
                'Page',
                [7, 8, 9], ['x', 'y', 'z'],
                'Finish']
    printer = MockPrinter()
    printer.Print(resource)
    actual = printer.GetTestOutput()
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  resource_printer_test_base.main()

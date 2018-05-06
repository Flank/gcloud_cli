# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for the core.resource.resource_reference module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_reference
from tests.lib import test_case


class ResourceReferenceTest(test_case.TestCase):

  def testGetReferencedKeyNamesNone(self):
    expected = set()
    actual = resource_reference.GetReferencedKeyNames()
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFilter(self):
    expected = {'ABC', 'pdq'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq<123]',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFormat(self):
    expected = {'abc.xyz', 'def', 'pdq'}
    actual = resource_reference.GetReferencedKeyNames(
        format_string='table(abc.xyz:label=ABC, def, pdq)',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFilterFormat(self):
    expected = {'abc.xyz', 'def', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq<123 OR rst:no]',
        format_string='table(abc.xyz:label=ABC, def, pdq)',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFilterPrinter(self):
    expected = {'abc.xyz', 'def', 'pdq', 'rst'}
    printer = resource_printer.Printer('table(abc.xyz:label=ABC, def, pdq)')
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq<123 OR rst:no]',
        printer=printer,
        defaults=printer.column_attributes,
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFilterFormatPrinter(self):
    printer = resource_printer.Printer('table(abc.xyz:label=ABC, def, pdq)')
    with self.assertRaisesRegex(ValueError, ''):
      resource_reference.GetReferencedKeyNames(
          filter_string='ABC:xyz OR pdq<123 OR rst:no]',
          format_string='table(abc.xyz:label=ABC, def, pdq)',
          printer=printer,
          defaults=printer.column_attributes,
      )

  def testGetReferencedKeyNamesFilterFormatDisable(self):
    expected = {'abc.xyz', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq<123 OR rst:no',
        format_string='table(abc.xyz:label=ABC, def, pdq) disable',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesFilterFormatList(self):
    expected = {'abc.xyz', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq<123 OR rst:no',
        format_string='table(abc.xyz:label=ABC, def, pdq) list',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesRepeatedFilterFormat(self):
    expected = {'abc.xyz', 'def', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq[2]<123 OR rst:no',
        format_string='table(abc[].xyz:label=ABC, def, pdq)',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesRepeatedFilterFormatDisable(self):
    expected = {'abc.xyz', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq[2]<123 OR rst:no',
        format_string='table(abc[].xyz:label=ABC, def, pdq) disable',
    )
    self.assertEqual(expected, actual)

  def testGetReferencedKeyNamesRepeatedFilterFormatList(self):
    expected = {'abc.xyz', 'pdq', 'rst'}
    actual = resource_reference.GetReferencedKeyNames(
        filter_string='ABC:xyz OR pdq[2]<123 OR rst:no',
        format_string='table(abc[].xyz:label=ABC, def, pdq) list',
    )
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()

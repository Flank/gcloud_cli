# -*- coding: utf-8 -*- #
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
"""Unit tests for arg parsing utilities for service-management."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.endpoints import arg_parsers

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class ServiceManagementArgParsersTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for service management arg parsing utilities."""

  def testGetServiceNameFromArg(self):
    expected = 'myservice'
    actual = arg_parsers.GetServiceNameFromArg('services/myservice')
    self.assertEqual(expected, actual)

  def testGetServiceNameFromArgSimpleInput(self):
    expected = 'myservice'
    actual = arg_parsers.GetServiceNameFromArg('myservice')
    self.assertEqual(expected, actual)

  def testGetServiceNameFromArgNonetypeInput(self):
    expected = None
    actual = arg_parsers.GetServiceNameFromArg(None)
    self.assertEqual(expected, actual)

  def testGetOperationIdFromArg(self):
    expected = 'myoperation'
    actual = arg_parsers.GetOperationIdFromArg('operations/myoperation')
    self.assertEqual(expected, actual)

  def testGetOperationIdFromArgSimpleInput(self):
    expected = 'myoperation'
    actual = arg_parsers.GetOperationIdFromArg('myoperation')
    self.assertEqual(expected, actual)

  def testGetOperationIdFromArgNonetypeInput(self):
    expected = None
    actual = arg_parsers.GetOperationIdFromArg(None)
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()

# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Test of the 'operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class OperationsDescribeUnitTest(unit_base.DataprocUnitTestBase):

  def _testDescribeOperation(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    expected = self.MakeCompletedOperation(region=region)
    self.ExpectGetOperation(expected, region=region)
    result = self.RunDataproc('operations describe {0} {1}'.format(
        self.OperationName(region=region), region_flag))
    self.AssertMessagesEqual(expected, result)

  def testDescribeOperation(self):
    self._testDescribeOperation()

  def testDescribeOperation_regionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testDescribeOperation(region='us-central1')

  def testDescribeOperation_regionFlag(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testDescribeOperation(
        region='us-east4', region_flag='--region=us-east4')

  def testDescribeOperation_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('operations describe foo', set_region=False)

  def testDescribeOperationNotFound(self):
    self.ExpectGetOperation(exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('operations describe ' + self.OperationName())

  def testOperationId(self):
    expected = self.MakeCompletedOperation()
    self.ExpectGetOperation(expected)
    result = self.RunDataproc('operations describe ' + self.OPERATION_ID)
    self.AssertMessagesEqual(expected, result)

  def testOperationUri(self):
    expected = self.MakeCompletedOperation()
    self.ExpectGetOperation(expected)
    result = self.RunDataproc('operations describe ' + self.OperationUri())
    self.AssertMessagesEqual(expected, result)


class OperationsDescribeUnitTestBeta(OperationsDescribeUnitTest,
                                     base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class OperationsDescribeUnitTestAlpha(OperationsDescribeUnitTestBeta,
                                      base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()

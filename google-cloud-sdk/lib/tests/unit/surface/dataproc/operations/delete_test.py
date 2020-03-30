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

"""Test of the 'operations delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class OperationsDeleteUnitTest(unit_base.DataprocUnitTestBase):

  def ExpectDeleteOperation(self,
                            operation_name=None,
                            exception=None,
                            region=None):
    if region is None:
      region = self.REGION
    if not operation_name:
      operation_name = self.OperationName(region=region)
    response = None
    if not exception:
      response = self.messages.Empty()
    self.mock_client.projects_regions_operations.Delete.Expect(
        self.messages.DataprocProjectsRegionsOperationsDeleteRequest(
            name=operation_name),
        response=response,
        exception=exception)

  def _testDeleteOperation(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    self.ExpectDeleteOperation(region=region)
    self.WriteInput('y\n')
    result = self.RunDataproc('operations delete {0} {1}'.format(
        self.OperationName(region=region), region_flag))
    self.AssertErrContains("The operation '{0}' will be deleted.".format(
        self.OperationName(region=region)))
    self.AssertErrContains('PROMPT_CONTINUE')
    self.assertIsNone(result)
    self.AssertErrContains(
        'Deleted [{0}].'.format(self.OperationName(region=region)))

  def testDeleteOperation(self):
    self._testDeleteOperation()

  def testDeleteOperation_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteOperation(region='global')

  def testDeleteOperation_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteOperation(
        region='us-central1', region_flag='--region=us-central1')

  def testDeleteOperation_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('operations delete foo', set_region=False)

  def testDeleteOperationDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Deletion aborted by user.'):
      self.RunDataproc('operations delete {0}'.format(self.OperationName()))
    self.AssertErrContains(
        "The operation '{0}' will be deleted.".format(self.OperationName()))

  def testDeleteOperationNotFound(self):
    self.ExpectDeleteOperation(
        self.OperationName(), exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('operations delete {0}'.format(self.OperationName()))

  def testOperationId(self):
    self.ExpectDeleteOperation()
    result = self.RunDataproc(
        'operations delete 564f9cac-e514-43e5-98de-e74442010cd3')
    self.assertIsNone(result)


class OperationsDeleteUnitTestBeta(OperationsDeleteUnitTest,
                                   base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class OperationsDeleteUnitTestAlpha(OperationsDeleteUnitTestBeta,
                                    base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()

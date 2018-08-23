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

"""Test of the 'operations cancel' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class OperationsCancelUnitTest(unit_base.DataprocUnitTestBase):

  def ExpectCancelOperation(self, name=None, exception=None):
    if not name:
      name = self.OperationName()
    response = None
    if not exception:
      response = self.messages.Empty()
    self.mock_client.projects_regions_operations.Cancel.Expect(
        self.messages.DataprocProjectsRegionsOperationsCancelRequest(name=name),
        response=response,
        exception=exception)

  def testCancelOperation(self):
    self.ExpectCancelOperation()
    self.WriteInput('y\n')
    result = self.RunDataproc(
        'operations cancel {0}'.format(self.OperationName()))
    self.AssertErrContains(
        "The operation '{0}' will be cancelled.".format(self.OperationName()))
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Cancelled [{0}].'.format(self.OperationName()))
    self.assertIsNone(result)

  def testCancelOperationDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Cancellation aborted by user.'):
      self.RunDataproc('operations cancel {0}'.format(self.OperationName()))
    self.AssertErrContains(
        "The operation '{0}' will be cancelled.".format(self.OperationName()))
    self.AssertErrContains('PROMPT_CONTINUE')

  def testCancelOperationNotFound(self):
    self.ExpectCancelOperation(
        self.OperationName(), exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('operations cancel ' + self.OperationName())

  def testOperationId(self):
    self.ExpectCancelOperation()
    result = self.RunDataproc(
        'operations cancel 564f9cac-e514-43e5-98de-e74442010cd3')
    self.assertIsNone(result)


class OperationsCancelUnitTestBeta(OperationsCancelUnitTest,
                                   base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

if __name__ == '__main__':
  sdk_test_base.main()

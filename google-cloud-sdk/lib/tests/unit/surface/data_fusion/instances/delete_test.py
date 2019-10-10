# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for instances delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.data_fusion import base


class InstancesDeleteBetaTest(base.InstancesUnitTest):

   # Must be called after self.SetTrack() for self.messages to be present
  def _SetTestMessages(self):
    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)

  def testSuccessfulDelete(self):
    self._SetTestMessages()
    self.WriteInput('y\n')
    successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.ExpectInstanceDelete(
        self.TEST_INSTANCE_NAME,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=successful_op)

    self.RunInstances('delete', self.TEST_INSTANCE,
                      '--location', self.TEST_LOCATION)

  def testDeleteInstanceNotFound(self):
    self.WriteInput('y\n')
    self.ExpectInstanceDelete(
        self.TEST_INSTANCE_NAME,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error, 'Resource not found API reason: NOT_FOUND'):
      self.RunInstances('delete', self.TEST_INSTANCE,
                        '--location', self.TEST_LOCATION)


if __name__ == '__main__':
  test_case.main()

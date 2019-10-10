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
"""Unit tests for instances create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.data_fusion import base


class InstancesCreateBetaTest(base.InstancesUnitTest):

  def _SetTestMessages(self):
    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)

  def testSuccessfulCreateSimple(self):
    """Tests a successful creation."""
    self._SetTestMessages()
    successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.ExpectInstanceCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        self.TEST_ZONE,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=successful_op)

    self.RunInstances('create', self.TEST_INSTANCE, '--location',
                      self.TEST_LOCATION, '--zone', self.TEST_ZONE)
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to '
        'complete. This may take several minutes."'.format(
            self.TEST_OPERATION_NAME))

  def testSuccessfulCreateAdvanced(self):
    self._SetTestMessages()
    successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.ExpectInstanceCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        self.TEST_ZONE,
        self.messages.Instance.TypeValueValuesEnum.ENTERPRISE,
        True,
        False,
        self.TEST_OPTIONS_DICT,
        self.TEST_OPTIONS_DICT,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=successful_op)

    self.RunInstances('create', self.TEST_INSTANCE, '--location',
                      self.TEST_LOCATION, '--zone', self.TEST_ZONE,
                      '--edition', self.TEST_TYPE,
                      '--enable_stackdriver_logging',
                      '--options', self.TEST_OPTIONS,
                      '--labels', self.TEST_OPTIONS)
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to '
        'complete. This may take several minutes."'.format(
            self.TEST_OPERATION_NAME))

  def testFailedCreate(self):
    self._SetTestMessages()
    error_msg = 'error message'
    failed_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True,
        error=self.messages.Status(message=error_msg))
    self.ExpectInstanceCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        self.TEST_ZONE,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=failed_op)

    with self.AssertRaisesExceptionRegexp(
        core_exceptions.Error,
        r'Operation \[{}] failed: {}'.format(
            self.TEST_OPERATION_NAME,
            error_msg)):
      self.RunInstances('create', self.TEST_INSTANCE, '--location',
                        self.TEST_LOCATION, '--zone', self.TEST_ZONE)


if __name__ == '__main__':
  test_case.main()

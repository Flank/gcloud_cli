# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for gcloud app services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib.surface.app import operations_base


class OperationsWaitTest(operations_base.OperationsTestBase):
  """Suite of tests around the 'app operations wait' command."""

  def SetUp(self):
    self.StartPatch('time.sleep')

  def testWait_NoProject(self):
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app operations wait o1')

  def testWaitOnFinishedCommand(self):
    """Tests case when command is already finished."""
    operation = self.MakeOperation(self.Project(), 'o1', True)
    self.ExpectGetOperationsRequest(self.Project(), 'o1', operation)
    self.Run('app operations wait o1')
    self.AssertErrContains('Operation [o1] is already done.')

  def testWaitOnPendingCommand(self):
    """Tests case when command is not already finished."""
    op_pending = self.MakeOperation(self.Project(), 'o1', False)
    op_finished = self.MakeOperation(self.Project(), 'o1', True)
    self.ExpectGetOperationsRequest(self.Project(), 'o1', op_pending)
    self.ExpectGetOperationsRequest(self.Project(), 'o1', op_finished)
    op = self.Run('app operations wait o1')

    # Wait command returns the finished command.
    self.assertTrue(op.done)
    self.assertEqual(op.name, 'apps/{}/operations/o1'.format(self.Project()))
    props = op.metadata.additionalProperties
    self.assertEqual(len(props), 1)
    self.assertEqual(props[0].key, 'insertTime')
    self.assertEqual(props[0].value, self.default_start_time)

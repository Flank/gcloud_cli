# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for gcloud app operations describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types

from googlecloudsdk.core import properties
from tests.lib.surface.app import operations_base


class OperationsDescribeTest(operations_base.OperationsTestBase):
  """Suite of tests around the 'app operations describe' command."""

  def SetUp(self):
    properties.VALUES.core.project.user_output_enabled = False

  def testDescribe_NoProject(self):
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app operations describe o1')

  def testDescribe(self):
    """Basic test to describe an operation."""
    operation = self.MakeOperation(self.Project(), 'o1', True)
    self.ExpectGetOperationsRequest(self.Project(), 'o1', operation)
    op = self.Run('app operations describe o1')
    self.assertEqual(operation, op)

  def testDescribeWithProperties(self):
    """Basic test to describe an operation."""
    method_value = extra_types.JsonValue(
        string_value='google.appengine.v1.Versions.UpdateVersion')
    target_value = extra_types.JsonValue(
        string_value='apps/{}/services/flex/versions/2023394'
        .format(self.Project()))
    insert_time = extra_types.JsonValue(
        string_value='2016-11-21T14:21:14.643Z')
    props = {'method': method_value,
             'target': target_value,
             'insertTime': insert_time}
    operation = self.MakeOperation(self.Project(),
                                   'o1', True, props=props)
    self.ExpectGetOperationsRequest(self.Project(), 'o1', operation)
    op = self.Run('app operations describe o1')
    self.assertEqual(operation, op)

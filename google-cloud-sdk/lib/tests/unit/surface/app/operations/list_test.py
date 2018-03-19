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
import textwrap

from apitools.base.py import encoding
from apitools.base.py import extra_types

from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.core import properties
from tests.lib.surface.app import operations_base


class OperationsListTest(operations_base.OperationsTestBase):
  """Suite of tests around the 'app operations list' command."""

  def testList_NoProject(self):
    self.UnsetProject()
    with self.assertRaisesRegexp(properties.RequiredPropertyError,
                                 'is not currently set.'):
      self.Run('app operations list')

  def testListOne(self):
    """Tests list when there's only one operation, without metadata."""
    operation = self.MakeOperation(self.Project(), 'o1', True,
                                   no_metadata=True)
    self.ExpectListOperationsRequest(
        self.Project(),
        self.MakeListOperationsResponse([operation]))
    self.Run('app operations list')

    self.AssertOutputEquals(textwrap.dedent("""\
        ID  START_TIME  STATUS
        o1              COMPLETED
        """))

  def testListMultiple(self):
    """Tests list when there's multiple operations."""
    o1 = self.MakeOperation(self.Project(), 'o1', True)
    o2 = self.MakeOperation(self.Project(), 'o2', True)
    o3 = self.MakeOperation(self.Project(), 'o3', True)
    self.ExpectListOperationsRequest(
        self.Project(),
        self.MakeListOperationsResponse([o1, o2, o3]))
    self.Run('app operations list')

    self.AssertOutputEquals(textwrap.dedent("""\
        ID  START_TIME                STATUS
        o1  2016-12-08T23:59:10.646Z  COMPLETED
        o2  2016-12-08T23:59:10.646Z  COMPLETED
        o3  2016-12-08T23:59:10.646Z  COMPLETED
        """))

  def testListMultipleMixedConfigurations(self):
    """Tests list for a variety of operations."""
    o1 = self.MakeOperation(self.Project(), 'o1', True)
    list_entry = encoding.PyValueToMessage(
        self.messages.Status.DetailsValueListEntry,
        {'additionalProperties': {'type@': 'type', 'info': 'info'}})
    error = self.messages.Status(
        code=500,
        details=[list_entry],
        message='Internal Server Error')
    o2 = self.MakeOperation(self.Project(), 'o2', True, error=error)
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
    o3 = self.MakeOperation(self.Project(), 'o3', True, props=props)
    o4 = self.MakeOperation(self.Project(), 'o4', False)
    o1_template = operations_util.Operation(o1)
    o2_template = operations_util.Operation(o2)
    o3_template = operations_util.Operation(o3)
    o4_template = operations_util.Operation(o4)
    self.ExpectListOperationsRequest(
        self.Project(),
        self.MakeListOperationsResponse([o1, o2, o3, o4]))
    operations = list(self.Run('app operations list --format=disable'))

    self.assertEquals(len(operations), 4)
    self.assertEquals(operations[0], o1_template)
    self.assertEquals(operations[1], o2_template)
    self.assertEquals(operations[2], o3_template)
    self.assertEquals(operations[3], o4_template)

  def testListOnlyPending(self):
    """Tests list for a variety of operations."""
    self.MakeOperation(self.Project(), 'o1', True)
    list_entry = encoding.PyValueToMessage(
        self.messages.Status.DetailsValueListEntry,
        {'additionalProperties': {'type@': 'type', 'info': 'info'}})
    error = self.messages.Status(
        code=500,
        details=[list_entry],
        message='Internal Server Error')
    self.MakeOperation(self.Project(), 'o2', True, error=error)
    o3 = self.MakeOperation(self.Project(), 'o3', False)
    o3_template = operations_util.Operation(o3)
    self.ExpectListOperationsRequest(
        self.Project(),
        self.MakeListOperationsResponse([o3]),
        filter_='done:false')
    operations = list(
        self.Run('app operations list --pending --format=disable'))

    self.assertEquals(len(operations), 1)
    self.assertEquals(operations[0], o3_template)

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
"""ml-engine operations list tests."""
from apitools.base.py import encoding

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class ListTestBase(object):

  def GetOperation(self, name, done=True):
    metadata_msg = self.short_msgs.OperationMetadata
    operation_type_enum = metadata_msg.OperationTypeValueValuesEnum
    return self.msgs.GoogleLongrunningOperation(
        name='projects/{}/operations/{}'.format(self.Project(), name),
        done=done,
        metadata=encoding.DictToMessage({
            'operationType': str(operation_type_enum.DELETE_MODEL),
            'createTime': '2016-01-01T00:00:00Z'
        }, self.msgs.GoogleLongrunningOperation.MetadataValue))

  def SetUp(self):
    self.client.projects_operations.List.Expect(
        self.msgs.MlProjectsOperationsListRequest(
            pageSize=100,
            name='projects/{}'.format(self.Project()),
        ),
        self.msgs.GoogleLongrunningListOperationsResponse(
            operations=[
                self.GetOperation('foo'),
                self.GetOperation('bar', done=False)
            ]))
    # So Run() returns resources
    properties.VALUES.core.user_output_enabled.Set(False)

  def testList(self):
    self.assertEqual(
        list(self.Run('ml-engine operations list')),
        [
            self.GetOperation('foo'),
            self.GetOperation('bar', done=False),
        ])

  def testList_DefaultFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)  # So we see the output

    self.Run('ml-engine operations list')

    self.AssertOutputEquals("""\
        NAME  OPERATION_TYPE  DONE
        foo   DELETE_MODEL    True
        bar   DELETE_MODEL    False
        """, normalize_space=True)


class ListGaTest(ListTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(ListGaTest, self).SetUp()


class ListBetaTest(ListTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ListBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()

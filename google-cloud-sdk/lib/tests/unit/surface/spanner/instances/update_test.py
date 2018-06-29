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
"""Tests for Spanner instances update command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import extra_types
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class InstancesUpdateTest(base.SpannerTestBase):
  """Cloud Spanner instances update tests."""

  def SetUp(self):
    self.ins_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')

  def testAsync(self):
    self.client.projects_instances.Patch.Expect(
        request=self.msgs.SpannerProjectsInstancesPatchRequest(
            name=self.ins_ref.RelativeName(),
            updateInstanceRequest=self.msgs.UpdateInstanceRequest(
                fieldMask='displayName,nodeCount',
                instance=self.msgs.Instance(
                    displayName='name', nodeCount=3))),
        response=self.msgs.Operation())
    self.Run('spanner instances update insId --nodes 3 --description name'
             ' --async')

  def testSync(self):
    op_ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.operations')
    self.client.projects_instances.Patch.Expect(
        request=self.msgs.SpannerProjectsInstancesPatchRequest(
            name=self.ins_ref.RelativeName(),
            updateInstanceRequest=self.msgs.UpdateInstanceRequest(
                fieldMask='displayName,nodeCount',
                instance=self.msgs.Instance(
                    displayName='name', nodeCount=3))),
        response=self.msgs.Operation(name=op_ref.RelativeName()))
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=op_ref.RelativeName()),
        response=self.msgs.Operation(
            name=op_ref.RelativeName(),
            done=True,
            response=self.msgs.Operation.ResponseValue(
                additionalProperties=[
                    self.msgs.Operation.ResponseValue.AdditionalProperty(
                        key='name',
                        value=extra_types.JsonValue(
                            string_value='resultname'))])))
    self.client.projects_instances.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name='resultname'),
        response=self.msgs.Instance())
    self.Run('spanner instances update insId --nodes 3 --description name')

# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib.surface.spanner import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class InstancesUpdateTest(base.SpannerTestBase):
  """Cloud Spanner instances update tests."""

  def SetUp(self):
    self.ins_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.op_ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.operations')

  def testAsync(self, track):
    self.track = track
    self.client.projects_instances.Patch.Expect(
        request=self.msgs.SpannerProjectsInstancesPatchRequest(
            name=self.ins_ref.RelativeName(),
            updateInstanceRequest=self.msgs.UpdateInstanceRequest(
                fieldMask='displayName,nodeCount',
                instance=self.msgs.Instance(displayName='name', nodeCount=3))),
        response=self.msgs.Operation(name=self.op_ref.RelativeName()))
    self.Run('spanner instances update insId --nodes 3 --description name'
             ' --async')
    # The current implementation(update.py) does not include the standard
    # LRO handling in gcloud, so only test Alpha track for update.yaml.
    if self.track == calliope_base.ReleaseTrack.ALPHA:
      self.AssertErrContains('Request issued for: [insId]')
      self.AssertErrContains('Check operation [{}] for status.'.format(
          self.op_ref.RelativeName()))
      self.AssertErrContains('Updated instance [insId].\n')

  def testSync(self, track):
    self.track = track
    self.client.projects_instances.Patch.Expect(
        request=self.msgs.SpannerProjectsInstancesPatchRequest(
            name=self.ins_ref.RelativeName(),
            updateInstanceRequest=self.msgs.UpdateInstanceRequest(
                fieldMask='displayName,nodeCount',
                instance=self.msgs.Instance(displayName='name', nodeCount=3))),
        response=self.msgs.Operation(name=self.op_ref.RelativeName()))
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=self.op_ref.RelativeName()),
        response=self.msgs.Operation(
            name=self.op_ref.RelativeName(),
            done=True,
            response=self.msgs.Operation.ResponseValue(additionalProperties=[
                self.msgs.Operation.ResponseValue.AdditionalProperty(
                    key='name',
                    value=extra_types.JsonValue(
                        string_value=self.ins_ref.RelativeName()))
            ])))
    self.client.projects_instances.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesGetRequest(
            name=self.ins_ref.RelativeName()),
        response=self.msgs.Instance())
    self.Run('spanner instances update insId --nodes 3 --description name')
    # The current implementation(update.py) does not include the standard
    # LRO handling in gcloud, so only test Alpha track for update.yaml.
    if self.track == calliope_base.ReleaseTrack.ALPHA:
      self.AssertErrContains('Request issued for: [insId]')
      self.AssertErrContains('Updated instance [insId].\n')

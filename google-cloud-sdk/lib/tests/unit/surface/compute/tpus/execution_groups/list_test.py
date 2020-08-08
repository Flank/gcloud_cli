# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib.surface.compute.tpus import base


class ListTest(base.TpuUnitTestBase):

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.instances_messages = core_apis.GetMessagesModule(
        'compute', self.compute_api_version)
    self.mock_instance_client = mock.Client(
        core_apis.GetClientClass('compute', self.compute_api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.compute_api_version, no_http=True))
    self.mock_instance_client.Mock()
    self.addCleanup(self.mock_instance_client.Unmock)
    properties.VALUES.core.user_output_enabled.Set(True)

  def fully_qualified_node_name(self, name):
    return 'projects/fake-projects/locations/central2-a/nodes/{}'.format(name)

  def _expectTPUNodesListCall(self):
    self.mock_tpu_client.projects_locations_nodes.List.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesListRequest(
            pageSize=100,
            parent='projects/fake-project/locations/central2-a'),
        response=self.tpu_messages.ListNodesResponse(nodes=[
            self.tpu_messages.Node(name='status-paused--invalid-node-name'),
            self.tpu_messages.Node(
                name=self.fully_qualified_node_name('will-not-be-listed')),
            self.tpu_messages.Node(
                name=self.fully_qualified_node_name(
                    'tpu-only-no-vm-will-not-be-listed')),
            self.tpu_messages.Node(
                name=self.fully_qualified_node_name('status-running'),
                state=self.tpu_messages.Node.StateValueValuesEnum.READY,
                ipAddress='random-fake-ip'),
            self.tpu_messages.Node(
                name=self.fully_qualified_node_name(
                    'status-unknown--tpu-not-running'),
                state=self.tpu_messages.Node.StateValueValuesEnum.TERMINATED),
            self.tpu_messages.Node(
                name=self.fully_qualified_node_name(
                    'status-unknown--vm-not-running'),
                state=self.tpu_messages.Node.StateValueValuesEnum.READY,
                ipAddress='random-fake-ip'),
        ]))

  def _expectInstanceListCall(self):
    labels = self.instances_messages.Instance.LabelsValue(additionalProperties=[
        self.instances_messages.Instance.LabelsValue.AdditionalProperty(
            key='ctpu', value='randomValue')
    ])
    self.mock_instance_client.instances.List.Expect(
        request=self.instances_messages.ComputeInstancesListRequest(
            maxResults=100,
            project=u'fake-project',
            zone=u'central2-a'),
        exception=None,
        response=self.instances_messages.InstanceList(items=[
            self.instances_messages.Instance(
                name='status-paused--invalid-node-name', labels=labels),
            self.instances_messages.Instance(
                name='status-paused--only-vm-present', labels=labels),
            self.instances_messages.Instance(name='will-not-be-listed'),
            self.instances_messages.Instance(
                name='status-running',
                labels=labels,
                status=self.instances_messages.Instance.StatusValueValuesEnum
                .RUNNING),
            self.instances_messages.Instance(
                name='status-unknown--tpu-not-running',
                labels=labels,
                status=self.instances_messages.Instance.StatusValueValuesEnum
                .RUNNING),
            self.instances_messages.Instance(
                name='status-unknown--vm-not-running',
                labels=labels,
                status=self.instances_messages.Instance.StatusValueValuesEnum
                .TERMINATED),
        ]))

  def testListCommand(self):
    self._expectInstanceListCall()
    self._expectTPUNodesListCall()
    self.Run("""
      compute tpus execution-groups list --zone=central2-a
    """)

    self.AssertOutputEquals("""\
    NAME STATUS
    status-paused--invalid-node-name Paused
    status-paused--only-vm-present Paused
    status-running Running
    status-unknown--tpu-not-running Unknown Status
    status-unknown--vm-not-running Unknown Status
    """, normalize_space=True)
